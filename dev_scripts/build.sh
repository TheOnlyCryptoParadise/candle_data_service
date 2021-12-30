python -m build
docker build . -t lewelyn/cryptoparadise-candle_data_service:latest --build-arg CACHEBUST=$(date +%s)