@echo off
echo Starting Registry service on port 10000...
start "Registry (10000)" .venv\Scripts\python -m registry

timeout /t 2 /nobreak > nul

echo Starting Tax Agent on port 10102...
start "Tax Agent (10102)" .venv\Scripts\python -m tax_agent

echo Starting Compliance Agent on port 10103...
start "Compliance Agent (10103)" .venv\Scripts\python -m compliance_agent

timeout /t 3 /nobreak > nul

echo Starting Law Agent on port 10101...
start "Law Agent (10101)" .venv\Scripts\python -m law_agent

timeout /t 3 /nobreak > nul

echo Starting Customer Agent on port 10100...
start "Customer Agent (10100)" .venv\Scripts\python -m customer_agent

echo All services started in separate windows!
echo Keep those windows open while testing.
