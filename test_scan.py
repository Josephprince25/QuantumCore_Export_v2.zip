from main import run_analysis
import json
import logging

logging.basicConfig(level=logging.INFO)

print("Running test scan...")
results = run_analysis(['MEXC', 'Binance']) # Test just two to be faster
print(f"Profitable count: {len(results['profitable'])}")
print(f"All paths count: {len(results['all_paths'])}")

if results['all_paths']:
    print("Sample Path:")
    print(json.dumps(results['all_paths'][0], indent=2))
else:
    print("No paths found.")
