class DPIDConverter:
    @staticmethod
    def to_hex(dpid_int: int) -> str:
        """
        Chuyen doi so nguyen sang chuoi Hex 16 ky tu chuan cua Ryu.
        Vi du: 1 -> "0000000000000001"
        """
        # ":016x" nghia la format thanh chuoi hex (x) in thuong, do dai 16, dien so 0 vao cho trong
        return f"{dpid_int:016x}"

    @staticmethod
    def to_int(dpid_hex: str) -> int:
        """
        Chuyen doi chuoi Hex tu Ryu tra ve sang so nguyen.
        Vi du: "0000000000000001" -> 1
        """
        if not dpid_hex:
            return 0
        # Ham int(string, base) giup ep kieu chuoi hex (he 16) ve so nguyen (he 10)
        return int(dpid_hex, 16)
