import logging
import os
import grpc
import grpc_excel2csv_pb2
import grpc_excel2csv_pb2_grpc

def get_filepath(filename, extension, dir=os.path.dirname(__file__)):
  return os.path.abspath(f'{dir}/../test/{filename}{extension}')

def read_iterfile(filepath, chunk_size=1024):
  split_data = os.path.splitext(filepath)
  filename = split_data[0]
  extension = split_data[1]

  metadata = grpc_excel2csv_pb2.MetaData(filename=filename, extension=extension)
  yield grpc_excel2csv_pb2.UploadFileRequest(metadata=metadata)
  fullpath = get_filepath(filename, extension)
  with open(fullpath, mode="rb") as f:
    while True:
      chunk = f.read(chunk_size)
      if chunk:
        entry_request = grpc_excel2csv_pb2.UploadFileRequest(chunk_data=chunk)
        yield entry_request
      else:  # The chunk was empty, which means we're at the end of the file
        return

def run():

  with grpc.insecure_channel('[::1]:50051') as channel:
    stub = grpc_excel2csv_pb2_grpc.Excel2CsvStub(channel)
    response = stub.SayHello(grpc_excel2csv_pb2.HelloRequest())
    print("Greeter client received: " + response.message)

    filepath = get_filepath('test', '.csv')
    data = bytearray()
    for response in stub.Convert(read_iterfile('test.xlsx')):
      data.extend(response.chunk_data)

    with open(filepath, 'wb') as f:
      f.write(data)

if __name__ == '__main__':
  logging.basicConfig()
  print(f'cwd = {os.getcwd()}')
  run()