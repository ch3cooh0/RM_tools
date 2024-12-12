class 戦闘結果詳細:
    def __init__(self):
        # T4
        self.T4_歩兵数 = 0
        self.T4_歩兵被害数 = 0
        self.T4_弓兵数 = 0
        self.T4_弓兵被害数 = 0
        self.T4_騎兵数 = 0
        self.T4_騎兵被害数 = 0
        self.T4_攻城数 = 0
        self.T4_攻城被害数 = 0
        # T3
        self.T3_歩兵数 = 0
        self.T3_歩兵被害数 = 0
        self.T3_弓兵数 = 0
        self.T3_弓兵被害数 = 0
        self.T3_騎兵数 = 0
        self.T3_騎兵被害数 = 0
        self.T3_攻城数 = 0
        self.T3_攻城被害数 = 0
        # T2
        self.T2_歩兵数 = 0
        self.T2_歩兵被害数 = 0
        self.T2_弓兵数 = 0
        self.T2_弓兵被害数 = 0
        self.T2_騎兵数 = 0
        self.T2_騎兵被害数 = 0
        self.T2_攻城数 = 0
        self.T2_攻城被害数 = 0
        # T1
        self.T1_歩兵数 = 0
        self.T1_歩兵被害数 = 0
        self.T1_弓兵数 = 0
        self.T1_弓兵被害数 = 0
        self.T1_騎兵数 = 0
        self.T1_騎兵被害数 = 0
        self.T1_攻城数 = 0
        self.T1_攻城被害数 = 0

        # メタ情報
        self.is_me = False

    def set_is_me(self, is_me: bool):
        self.is_me = is_me

    def 参戦数_to_tsv_str(self) -> str:
        参戦人数 = "\t".join([str(self.T4_歩兵数), str(self.T4_弓兵数), str(self.T4_騎兵数), str(self.T4_攻城数), str(self.T3_歩兵数), str(self.T3_弓兵数), str(self.T3_騎兵数), str(self.T3_攻城数), str(self.T2_歩兵数), str(self.T2_弓兵数), str(self.T2_騎兵数), str(self.T2_攻城数), str(self.T1_歩兵数), str(self.T1_弓兵数), str(self.T1_騎兵数), str(self.T1_攻城数)])
        return f"{参戦人数}"
    
    def 被害数_to_tsv_str(self) -> str:
        被害人数 = "\t".join([str(self.T4_歩兵被害数), str(self.T4_弓兵被害数), str(self.T4_騎兵被害数), str(self.T4_攻城被害数), str(self.T3_歩兵被害数), str(self.T3_弓兵被害数), str(self.T3_騎兵被害数), str(self.T3_攻城被害数), str(self.T2_歩兵被害数), str(self.T2_弓兵被害数), str(self.T2_騎兵被害数), str(self.T2_攻城被害数), str(self.T1_歩兵被害数), str(self.T1_弓兵被害数), str(self.T1_騎兵被害数), str(self.T1_攻城被害数)])
        return f"{被害人数}"

