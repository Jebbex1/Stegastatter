import bpcs.engine as engine
import steganalysis.bit_plane_slicing as bps

if __name__ == '__main__':
    a = 0.3
    vessel_path = "assets/ves1.png"
    stegged_path = "assets/out1.png"
    output_path = "assets/message_out.txt"
    data_path = "assets/message.txt"

    data = open(data_path, "rb").read()

    token = engine.encode(vessel_path, data, stegged_path, b"KEYYY", alpha=a)

    output_data = engine.decode(stegged_path, token)

    open(output_path, "wb").write(output_data)
