wget https://circleci.com/api/v1.1/project/github/TheOnlyCryptoParadise/protos/latest/artifacts/0/dist/grpc_generated.tar
tar -xvf grpc_generated.tar
rm -r ../candle_data_service/grpc_generated
mv grpc_generated ../candle_data_service/
rm grpc_generated.tar