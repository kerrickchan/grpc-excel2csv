import os
import logging
import pandas as pd
import grpc
import grpc_excel2csv_pb2
import grpc_excel2csv_pb2_grpc

from concurrent import futures

def get_filepath(filename, extension, dir=os.path.dirname(__file__)):
  return os.path.abspath(f'{dir}/../.cache/{filename}{extension}')

class Excel2Csv(grpc_excel2csv_pb2_grpc.Excel2CsvServicer):
  def SayHello(self, request, context):
    return grpc_excel2csv_pb2.HelloResponse(message='Hello World')

  def Convert(self, request_iterator, context):
    # Cache data stream in from source
    data = bytearray()

    filepath_excel = ''
    for request in request_iterator:
      if request.metadata.filename and request.metadata.extension:
        filepath_excel = get_filepath(request.metadata.filename, request.metadata.extension)
        continue
      data.extend(request.chunk_data)
    with open(filepath_excel, 'wb') as f:
      f.write(data)

    # Convert
    df = pd.read_excel(filepath_excel)
    filename_csv = os.path.splitext(os.path.basename(filepath_excel))[0]
    filepath_csv = get_filepath(filename_csv, '.csv')
    df.to_csv(filepath_csv, index=None, header=True)

    # Response data stream in csv
    chunk_size = 1024

    with open(filepath_csv, mode="rb") as f:
      while True:
        chunk = f.read(chunk_size)
        if chunk:
          yield grpc_excel2csv_pb2.FileResponse(chunk_data=chunk)
        else:  # The chunk was empty, which means we're at the end of the file
          return

def serve():
  port = "50051"
  server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
  grpc_excel2csv_pb2_grpc.add_Excel2CsvServicer_to_server(Excel2Csv(), server)
  server.add_insecure_port("[::]:" + port)
  server.start()
  print("Server started, listening on " + port)
  server.wait_for_termination()

if __name__ == "__main__":
  logging.basicConfig()
  print(f'cwd = {get_filepath("", "")}')
  serve()
