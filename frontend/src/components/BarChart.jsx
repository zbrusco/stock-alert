import { createChart, CandlestickSeries } from "lightweight-charts";
import React, { useEffect, useRef } from "react";

let symbol = "AAPL";
let timeframe = "1D";
let start = "2025-01-01";
let end = "2025-01-11";

const MyCandleChart = () => {
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);
  const candleSeriesRef = useRef(null);
  const markersRef = useRef(null);

  useEffect(() => {
    // Create chart
    chartRef.current = createChart(chartContainerRef.current, {
      width: 800,
      height: 400,
      layout: {
        backgroundColor: "#ffffff",
        textColor: "#000",
      },
      grid: {
        vertLines: { color: "#eee" },
        horzLines: { color: "#eee" },
      },
      rightPriceScale: {
        borderColor: "#ccc",
      },
      timeScale: {
        borderColor: "#ccc",
      },
    });

    // Add candlestick series
    candleSeriesRef.current = chartRef.current.addSeries(CandlestickSeries, {
      upColor: "#26a69a",
      downColor: "#ef5350",
      borderVisible: false,
      wickVisible: true,
    });

    // Cleanup on unmount
    return () => {
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const resp = await fetch(
          `http://127.0.0.1:8000/data/get-ticker/${symbol}/?timeframe=${timeframe}&start=${start}&end=${end}`
        );
        const json = await resp.json();

        // Map data to Lightweight Charts format
        const formattedData = json.map((item) => ({
          time: Math.floor(new Date(item.timestamp).getTime() / 1000),
          open: item.open,
          high: item.high,
          low: item.low,
          close: item.close,
          volume: item.volume,
        }));

        candleSeriesRef.current.setData(formattedData);
      } catch (err) {
        console.error("Failed to fetch OHLCV data", err);
      }
    };

    fetchData();
  }, []);

  return <div ref={chartContainerRef} />;
};

export default MyCandleChart;
