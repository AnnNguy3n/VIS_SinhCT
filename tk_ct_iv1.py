from generator import Generator
import func
import pandas as pd
import numpy as np
import json


def convert_CT(CT, op_name):
    ret = ""
    temp = ["+", "-", "*", "/"]
    k = 0
    for e in CT:
        if k % 2 == 0:
            ret += temp[e]
        else:
            ret += "'" + op_name[e] + "'"

        k += 1

    return ret


def invest(self: Generator, weight, threshold):
    INDEX = self.INDEX
    temp_index = []
    reason = 0
    for i in range(INDEX.shape[0]-2):
        inv_cyc_val = weight[INDEX[-i-3]:INDEX[-i-2]]
        inv_cyc_sym = self.SYMBOL[self.INDEX[-i-3]:self.INDEX[-i-2]]
        if reason == 0: # Không đầu tư do không có công ty nào vượt ngưỡng 2 năm liền
            pre_cyc_val = weight[INDEX[-i-2]:INDEX[-i-1]]
            pre_cyc_sym = self.SYMBOL[self.INDEX[-i-2]:self.INDEX[-i-1]]
            a = np.where(pre_cyc_val > threshold)[0]
            b = np.where(inv_cyc_val > threshold)[0]
            coms = np.intersect1d(pre_cyc_sym[a], inv_cyc_sym[b])
        else:
            b = np.where(inv_cyc_val > threshold)[0]
            coms = inv_cyc_sym[b]

        if len(coms) == 0:
            temp_index.append(np.array([-1]))
            if reason == 0 and b.shape[0] == 0:
                reason = 1
        else:
            index = np.where(np.isin(inv_cyc_sym, coms, True))[0]
            index += INDEX[-i-3]
            temp_index.append(index)
            if reason == 1:
                reason = 0

    return temp_index


def tong_ket_file_cong_thuc(df_CT: pd.DataFrame, data: pd.DataFrame, nam_lay_nguong: int, folder):
    data_2 = data[data["TIME"] <= (nam_lay_nguong + 1)].reset_index(drop=True)

    vis = Generator(data, 1, [], False, 1, 1.06, 0, -1.0, max_loop=7)
    vis_2 = Generator(data_2, 1, [], False, 1, 1.06, 0, -1.0, max_loop=7)

    for k in range(len(df_CT)):
        weight = func.calculate_formula(vis.convert_strF_to_arrF(df_CT.formula[k]), vis.OPERAND)
        _1, _2, _3, threshold = vis_2._Generator__investment_method_1(weight[len(data) - len(data_2):], 0)
        list_index = invest(vis, weight, threshold)

        ret = {}
        ret["CT_string"] = convert_CT(vis.convert_strF_to_arrF(df_CT.formula[k]), vis.operand_name)
        ret["CT"] = df_CT.formula[k]
        ret["Invest_"] = {}
        total_profit = 1.0
        for i in range(len(list_index)):
            ret["Invest_"][2008+i] = {}
            if len(list_index[i]) == 1 and list_index[i][0] == -1:
                ret["Invest_"][2008+i]["Gui_ngan_hang"] = {}
                ret["Invest_"][2008+i]["Gui_ngan_hang"]["Value"] = 0.0
                ret["Invest_"][2008+i]["Gui_ngan_hang"]["Profit"] = vis.interest_rate
                total_profit *= 1.06
            else:
                for idx in list_index[i]:
                    ret["Invest_"][2008+i][vis.data.SYMBOL[idx]] = {}
                    ret["Invest_"][2008+i][vis.data.SYMBOL[idx]]["Value"] = weight[idx]
                    ret["Invest_"][2008+i][vis.data.SYMBOL[idx]]["Profit"] = vis.PROFIT[idx]
                
                total_profit *= np.mean(vis.PROFIT[list_index[i]])
            
            if 2008 + i == 2022:
                ret["Geomean_profit"] = total_profit ** (1.0/((len(list_index) - 1)))
        
        ret[f"Nguong_CT ({nam_lay_nguong})"] = threshold
        ret["TF_ratio"] = df_CT.tf_ratio[k]
        ret["Invest"] = ret["Invest_"]
        del(ret["Invest_"])
        with open(f"{folder}/CT_{k}.json", "w") as f:
            json.dump(ret, f, indent=4)