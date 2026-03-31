import networkx as nx
import matplotlib.pyplot as plt
import os


def generate_network_diagram(
    topo_json: dict, filename: str = "network_diagram.png"
) -> str:
    """
    Hàm đọc JSON từ Ryu và vẽ sơ đồ mạng ra file ảnh.
    """
    # 1. Khởi tạo đồ thị vô hướng (Undirected Graph)
    # Vì Mininet trả về 2 link cho 1 kết nối (A->B và B->A), đồ thị vô hướng sẽ gộp chúng lại thành 1 nét vẽ.
    G = nx.Graph()

    # 2. Bóc tách dữ liệu JSON để lấy các cạnh (Edges)
    for link in topo_json.get("links", []):
        # MẸO KỸ SƯ: Lấy "s1-eth1" cắt bỏ phần sau dấu "-" để lấy đúng chữ "s1"
        src_node = link["src"]["name"].split("-")[0]
        dst_node = link["dst"]["name"].split("-")[0]

        G.add_edge(src_node, dst_node)

    # 3. Phân loại màu sắc cho trực quan
    # Core Switch (s1) màu Đỏ nhạt, Access Points (ap1, ap2) màu Xanh dương nhạt
    node_colors = []
    for node in G.nodes():
        if node.startswith("s"):
            node_colors.append("lightcoral")
        else:
            node_colors.append("lightskyblue")

    # 4. Bắt đầu vẽ ảnh
    plt.figure(figsize=(8, 6))  # Kích thước khung hình

    # Layout thuật toán lò xo (Spring) giúp các Node tản ra nhìn đẹp mắt nhất
    pos = nx.spring_layout(G, seed=42)

    # Vẽ Node, Cạnh và Chữ
    nx.draw(
        G,
        pos,
        with_labels=True,
        node_color=node_colors,
        node_size=3500,  # Độ to của hình tròn
        font_size=12,
        font_weight="bold",
        edge_color="gray",
        width=2.5,  # Độ dày của dây mạng
    )

    plt.title("Sơ Đồ Hạ Tầng Mạng SDN", fontsize=16, fontweight="bold", pad=20)

    # 5. Lưu ra file ảnh và dọn dẹp RAM
    output_path = os.path.join(os.getcwd(), filename)
    plt.savefig(output_path, format="PNG", bbox_inches="tight")
    plt.close()  # Rất quan trọng để tránh tràn RAM khi gọi API nhiều lần

    return output_path
