/* eslint-disable @typescript-eslint/no-explicit-any */
import { createContext, useContext } from "react";

export type FormValues = Record<string, any>;

export type FormContextType = {
    values: FormValues;
    setValue: (name: string, value: any) => void;
    register: (name: string, initial?: any) => void;
    getValue: (name: string) => any;
};

const FormContext = createContext<FormContextType | undefined>(undefined);

export function useForm(): FormContextType | undefined {
    const ctx = useContext(FormContext);
    return ctx;
}

export { FormContext };
