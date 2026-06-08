import styles from "./OrderReports.module.scss";
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
} from "recharts";

const chartData = [
    { date: "Jan 1", orders: 45, revenue: 1200 },
    { date: "Jan 2", orders: 52, revenue: 1400 },
    { date: "Jan 3", orders: 48, revenue: 1300 },
    { date: "Jan 4", orders: 61, revenue: 1700 },
    { date: "Jan 5", orders: 55, revenue: 1500 },
    { date: "Jan 6", orders: 67, revenue: 1900 },
    { date: "Jan 7", orders: 72, revenue: 2100 },
];

export default function OrderReports() {
    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <h1>📊 Order Reports</h1>
                <p className={styles.subtitle}>
                    View sales reports and analytics
                </p>
            </div>
            <div className={styles.content}>
                <div className={styles.chartContainer}>
                    <h2>Daily Orders & Revenue</h2>
                    <ResponsiveContainer width="100%" height={400}>
                        <LineChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="date" />
                            <YAxis />
                            <Tooltip />
                            <Legend />
                            <Line
                                type="monotone"
                                dataKey="orders"
                                stroke="#8884d8"
                                strokeWidth={2}
                                dot={{ fill: "#8884d8", r: 4 }}
                            />
                            <Line
                                type="monotone"
                                dataKey="revenue"
                                stroke="#82ca9d"
                                strokeWidth={2}
                                dot={{ fill: "#82ca9d", r: 4 }}
                            />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </div>
    );
}
