import json
import uuid
from rest_framework import status
from rest_framework.response import Response
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from pizza_management.ingredient.model import Ingredient
from pizza_management.ingredient.validators import IngredientCreateRequest
from pizza_management.ingredient.serializers import IngredientSerializer
from pizza_management.shared.firebase_service import FirebaseStorageService
from pizza_management.shared.image_processor import ImageProcessor
from helper.auth_decorators import jwt_authentication, role_required
from helper.cache_helpers import CacheHelper
from pizza_management.ingredient.tasks import process_ingredient_import_async, cancel_ingredient_import


class CreateMixin:
    """Mixin for CREATE operations: create, import_json"""
    
    @jwt_authentication
    @role_required(["admin", "manager"])
    def create(self, request, *args, **kwargs):
        """POST /ingredients/ - Create ingredient with optional image upload (ADMIN ONLY)"""
        print("[Ingredient Create]: Running")
        try:
            image_file = request.FILES.get('image_file')
            piece_file = request.FILES.get('piece_file')
            
            form_data = self._normalize_form_data(request.data)
            valid_data = IngredientCreateRequest(**form_data)
            ingredient_dict = valid_data.model_dump(exclude_none=True)
            
            # Validate image files
            if image_file:
                FirebaseStorageService.is_valid_image(image_file)
            if piece_file:
                FirebaseStorageService.is_valid_image(piece_file)
            
            uploaded_urls = {}
            image_url = None
            piece_url = None
            
            try:
                if image_file:
                    image_url = ImageProcessor.upload_image(image_file, "ingredients")
                    if image_url:
                        uploaded_urls['image_url'] = image_url

                if piece_file:
                    piece_url = ImageProcessor.upload_image(piece_file, "ingredients")
                    if piece_url:
                        uploaded_urls['piece_url'] = piece_url
                        
                # Create ingredient
                ingredient = Ingredient.objects.create(
                    name=ingredient_dict['name'],
                    description=ingredient_dict.get('description'),
                    price=ingredient_dict['price'],
                    type=ingredient_dict['type'],
                    sub_type=ingredient_dict.get('sub_type'),
                    is_active=ingredient_dict.get('is_active', True),
                    image_url=image_url,
                    piece_image_url=piece_url,
                )
                print(f"✓ Ingredient created: {ingredient.id}")
                
                # Invalidate ingredients cache
                CacheHelper.cache_clear_pattern("ingredients_*")
                print("[CACHE] Invalidated all ingredients cache")
                
                return Response(IngredientSerializer(ingredient).data, status=status.HTTP_201_CREATED)
            
            except Exception as e:
                # Cleanup uploaded images if ingredient creation fails
                for url_type, url in uploaded_urls.items():
                    try:
                        FirebaseStorageService.delete_image(url)
                    except Exception as cleanup_err:
                        print(f"Error cleaning up {url_type}: {cleanup_err}")
                raise e
    
        except ValueError as e:
            print(f"❌ ValueError: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @jwt_authentication
    @role_required(["admin", "manager"])
    def import_json(self, request):
        """POST /ingredients/import-json/ - Import ingredients from JSON (ADMIN ONLY)"""
        try:
            print("\n=== IMPORT JSON REQUEST ===")
            print(f"Request data type: {type(request.data)}")
            print(f"Request data keys: {list(request.data.keys()) if isinstance(request.data, dict) else 'N/A'}")
            
            ingredients_data = self._extract_ingredients_data(request)
            
            # Log sample ingredient for debugging
            if ingredients_data and len(ingredients_data) > 0:
                print(f"First ingredient keys: {list(ingredients_data[0].keys())}")
                print(f"First ingredient image_url: {ingredients_data[0].get('image_url')}")
                print(f"First ingredient image_source_url: {ingredients_data[0].get('image_source_url')}")
            
            if not isinstance(ingredients_data, list):
                return Response(
                    {"error": "ingredients must be a list"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            # Generate unique import_id for WebSocket tracking
            import_id = str(uuid.uuid4())
            
            print(f"[Import] Starting async import with import_id={import_id}, total_items={len(ingredients_data)}")
            
            # Queue async Celery task - returns immediately!
            process_ingredient_import_async.delay(ingredients_data, import_id)  # type: ignore[misc]
            
            print(f"[Import] Queued async task")
            print("=== IMPORT ACCEPTED (ASYNC) ===\n")
            
            # Return HTTP 202 Accepted with import_id for WebSocket connection
            return Response(
                {"import_id": import_id, "message": "Import started in background"},
                status=status.HTTP_202_ACCEPTED,
            )
        
        except Exception as e:
            print(f"❌ Import failed to start: {str(e)}")
            import_id = str(uuid.uuid4())
            self._broadcast_import_error(import_id, str(e))
            return Response(
                {"error": f"Import failed to start: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @jwt_authentication
    @role_required(["admin", "manager"])
    def cancel_import(self, request, import_id=None):
        """POST /ingredients/import-cancel/{import_id}/ - Cancel ongoing import (ADMIN ONLY)"""
        try:
            import_id = import_id or request.data.get('import_id')
            if not import_id:
                return Response(
                    {"error": "import_id required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            print(f"[Cancel] Processing cancel request for import_id={import_id}")
            
            # Call cancel function from tasks
            success, message = cancel_ingredient_import(import_id)
            
            if success:
                # Broadcast cancel message to client
                try:
                    channel_layer = get_channel_layer()
                    if channel_layer:
                        async_to_sync(channel_layer.group_send)(
                            f"ingredient_import_{import_id}",
                            {
                                "type": "import.cancelled",
                                "message": message,
                            }
                        )
                        print(f"[WS] Broadcast cancel message for {import_id}")
                    else:
                        print(f"[WS] No channel layer available, skipping cancel broadcast for {import_id}")
                except Exception as ws_err:
                    print(f"[WS] Failed to broadcast cancel: {ws_err}")
                
                return Response(
                    {
                        "success": True,
                        "message": message,
                        "import_id": import_id,
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {
                        "success": False,
                        "error": message,
                        "import_id": import_id,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        
        except Exception as e:
            print(f"[Cancel] Exception: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _extract_ingredients_data(self, request):
        """Extract ingredients list from JSON file or request body"""
        json_file = request.FILES.get('json_file')
        
        if json_file:
            file_content = json_file.read().decode('utf-8')
            data = json.loads(file_content)
            return data.get("ingredients", data) if isinstance(data, dict) else data
        
        if isinstance(request.data, list):
            return request.data
        
        if isinstance(request.data, dict) and "ingredients" in request.data:
            return request.data["ingredients"]
        
        form_data = self._normalize_form_data(request.data)
        return form_data.get("ingredients", [form_data] if form_data else [])

    def _process_ingredient_import(self, idx, ingredient_data, results, import_id, total_items):
        """Process single ingredient import"""
        try:
            # Pop file paths and URLs from data
            image_file_path = ingredient_data.pop('image_file', None)
            piece_file_path = ingredient_data.pop('piece_file', None)
            image_url = ingredient_data.pop('image_url', None)
            piece_image_url = ingredient_data.pop('piece_image_url', None)
            
            valid_data = IngredientCreateRequest(**ingredient_data)
            ingredient_dict = valid_data.model_dump(exclude_none=True)
            
            # Process image_url (prioritize URL over file path)
            processed_image_url = None
            if image_url:
                if image_url.startswith(('http://', 'https://')):
                    print(f"[Import {idx}] Download + upload image from URL: {image_url}")
                    processed_image_url = ImageProcessor.download_and_upload_image(image_url, "ingredients")
                else:
                    print(f"[Import {idx}] Process image from path: {image_url}")
                    processed_image_url = ImageProcessor.process_image_path(image_url, "ingredients")
            elif image_file_path:
                print(f"[Import {idx}] Process image file: {image_file_path}")
                processed_image_url = ImageProcessor.process_image_path(image_file_path, "ingredients")
            
            # Process piece_image_url (prioritize URL over file path)
            processed_piece_url = None
            if piece_image_url:
                if piece_image_url.startswith(('http://', 'https://')):
                    print(f"[Import {idx}] Download + upload piece image from URL: {piece_image_url}")
                    processed_piece_url = ImageProcessor.download_and_upload_image(piece_image_url, "ingredients")
                else:
                    print(f"[Import {idx}] Process piece image from path: {piece_image_url}")
                    processed_piece_url = ImageProcessor.process_image_path(piece_image_url, "ingredients")
            elif piece_file_path:
                print(f"[Import {idx}] Process piece image file: {piece_file_path}")
                processed_piece_url = ImageProcessor.process_image_path(piece_file_path, "ingredients")
            
            ingredient = Ingredient.objects.create(
                name=ingredient_dict['name'],
                description=ingredient_dict.get('description'),
                price=ingredient_dict['price'],
                type=ingredient_dict['type'],
                sub_type=ingredient_dict.get('sub_type'),
                is_active=ingredient_dict.get('is_active', True),
                image_url=processed_image_url,
                piece_image_url=processed_piece_url,
            )
            
            results["created"].append({
                "id": ingredient.id,
                "name": ingredient.name,
                "type": ingredient.type,
            })
            
            # Broadcast progress update via WebSocket
            current = idx + 1
            percentage = int((current / total_items) * 100)
            self._broadcast_import_progress(import_id, current, total_items, percentage, f"Processing: {ingredient.name}")
            
        except Exception as e:
            results["errors"].append({
                "index": idx,
                "name": ingredient_data.get("name", "Unknown"),
                "error": str(e)
            })
            
            # Broadcast progress update with error
            current = idx + 1
            percentage = int((current / total_items) * 100)
            self._broadcast_import_progress(import_id, current, total_items, percentage, f"Error: {str(e)}")

    def _normalize_form_data(self, data):
        """Extract single values from form data lists"""
        normalized = {}
        excluded_fields = {'image_url', 'piece_image_url'}
        
        for key, value in data.items():
            if key in excluded_fields:
                continue
            if isinstance(value, list) and len(value) > 0:
                val = value[0]
            else:
                val = value
            normalized[key] = None if val == '' else val
        
        return normalized

    def _broadcast_import_progress(self, import_id, current, total, percentage, message=""):
        """Broadcast import progress via WebSocket"""
        try:
            channel_layer = get_channel_layer()
            group_name = f"ingredient_import_{import_id}"
            if not channel_layer:
                print(f"[WS] No channel layer available, skipping progress broadcast for {import_id}")
                return

            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "import.progress",
                    "current": current,
                    "total": total,
                    "percentage": percentage,
                    "message": message,
                }
            )
            print(f"[WS] Broadcasted progress: {percentage}% ({current}/{total})")
        except Exception as e:
            print(f"[WS] Failed to broadcast progress: {str(e)}")

    def _broadcast_import_completion(self, import_id, total_created, total_errors):
        """Broadcast import completion via WebSocket"""
        try:
            channel_layer = get_channel_layer()
            group_name = f"ingredient_import_{import_id}"
            
            message_text = f"Import completed: {total_created} created"
            if total_errors > 0:
                message_text += f", {total_errors} errors"
            
            if not channel_layer:
                print(f"[WS] No channel layer available, skipping completion broadcast for {import_id}")
                return

            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "import.completed",
                    "total_created": total_created,
                    "total_errors": total_errors,
                    "message": message_text,
                }
            )
            print(f"[WS] Broadcasted completion: {message_text}")
        except Exception as e:
            print(f"[WS] Failed to broadcast completion: {str(e)}")

    def _broadcast_import_error(self, import_id, error_message):
        """Broadcast import error via WebSocket"""
        try:
            channel_layer = get_channel_layer()
            group_name = f"ingredient_import_{import_id}"
            if not channel_layer:
                print(f"[WS] No channel layer available, skipping error broadcast for {import_id}")
                return

            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "import.error",
                    "error": error_message,
                    "message": f"Import failed: {error_message}",
                }
            )
            print(f"[WS] Broadcasted error: {error_message}")
        except Exception as e:
            print(f"[WS] Failed to broadcast error: {str(e)}")