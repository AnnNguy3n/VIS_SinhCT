import numpy as np
from numba import njit
from numba.typed import List


@njit
def get_valid_op(struct, idx, start):
    valid_op = np.full(2, 0)
    valid_op[start-2:] = 1

    if idx // 2 <= struct[0,1] // 2:
        valid_op[1] = 0

    return np.where(valid_op == 1)[0] + 2


@njit
def get_valid_operand(formula, struct, idx, start, num_operand):
    valid_operand = np.full(num_operand, 0)
    valid_operand[start:num_operand] = 1

    for i in range(struct.shape[0]):
        if struct[i,2] + 2*struct[i,1] > idx:
            gr_idx = i
            break

    """
    Tránh hoán vị nhân chia trong một cụm
    """
    pre_op = formula[idx-1]
    if pre_op >= 2:
        if pre_op == 2:
            temp_idx = struct[gr_idx,2]
            if idx >= temp_idx + 2:
                valid_operand[0:formula[idx-2]] = 0
        else:
            temp_idx = struct[gr_idx,2]
            temp_idx_1 = temp_idx + 2*struct[gr_idx,3]
            if idx > temp_idx_1 + 2:
                valid_operand[0:formula[idx-2]] = 0

            """
            Tránh chia lại những toán hạng đã nhân ở trong cụm (chỉ phép chia mới check)
            """
            valid_operand[formula[temp_idx:temp_idx_1+1:2]] = 0

    """
    Tránh hoán vị cộng trừ các cụm, kể từ cụm thứ 2 trở đi
    """
    if gr_idx > 0:
        gr_check_idx = -1
        for i in range(gr_idx-1,-1,-1):
            if struct[i,0]==struct[gr_idx,0] and struct[i,1]==struct[gr_idx,1] and struct[i,3]==struct[gr_idx,3]:
                gr_check_idx = i
                break

        if gr_check_idx != -1:
            idx_ = 0
            while True:
                idx_1 = struct[gr_idx,2] + idx_
                idx_2 = struct[gr_check_idx,2] + idx_
                if idx_1 == idx:
                    valid_operand[0:formula[idx_2]] = 0
                    break

                if formula[idx_1] != formula[idx_2]:
                    break

                idx_ += 2

        """
        Tránh trừ đi những cụm đã cộng trước đó (chỉ ở trong trừ cụm mới check)
        """
        if struct[gr_idx,0] == 1 and idx + 2 == struct[gr_idx,2] + 2*struct[gr_idx,1]:
            list_gr_check = np.where((struct[:,0]==0) & (struct[:,1]==struct[gr_idx,1]) & (struct[:,3]==struct[gr_idx,3]))[0]
            for i in list_gr_check:
                temp_idx = struct[i,2] + 2*struct[i,1] - 2
                temp_idx_1 = struct[gr_idx,2] + 2*struct[gr_idx,1] - 2
                if (formula[struct[i,2]:temp_idx] == formula[struct[gr_idx,2]:temp_idx_1]).all():
                    valid_operand[formula[temp_idx]] = 0

    return np.where(valid_operand==1)[0]


@njit
def investment_method_0(weight, index, profit, interest_rate):
    size = index.shape[0]-1
    arr_index = np.zeros(size, dtype=np.int64)
    arr_value = np.zeros(size, dtype=np.float64)
    arr_profit = np.zeros(size, dtype=np.float64)

    for i in range(index.shape[0]-2, -1, -1):
        idx = index.shape[0]-2-i
        temp = weight[index[i]:index[i+1]]
        max_ = np.max(temp)
        max_idx = np.where(temp == max_)[0] + index[i]
        if max_idx.shape[0] == 1:
            arr_index[idx] = max_idx[0]
            arr_value[idx] = max_
            arr_profit[idx] = profit[max_idx[0]]
            if profit[max_idx[0]] <= 0.0:
                return arr_index, arr_value, arr_profit
        else:
            arr_index[idx] = -1
            arr_value[idx] = max_
            arr_profit[idx] = interest_rate

    return arr_index, arr_value, arr_profit


def split_posint_into_sum(n, arr, list_result):
    if np.sum(arr) == n:
        list_result.append(arr)
    else:
        idx = np.where(arr==0)[0][0]
        sum_ = np.sum(arr)
        if idx == 0:
            max_ = n
        else:
            max_ = arr[idx-1]

        max_ = min(n-sum_, max_)
        for i in range(max_, 0, -1):
            arr[idx] = i
            split_posint_into_sum(n, arr.copy(), list_result)


def create_struct(add_struct, sub_struct):
    struct = np.full((add_struct.shape[0]+sub_struct.shape[0], 4), -1)
    temp_val = 1
    for i in range(add_struct.shape[0]):
        struct[i,:] = np.array([0, add_struct[i], temp_val, add_struct[i]-1])
        temp_val += 2*struct[i,1]

    for i in range(sub_struct.shape[0]):
        temp_val_1 = add_struct.shape[0] + i
        struct[temp_val_1,:] = np.array([1, sub_struct[i], temp_val, sub_struct[i]-1])
        temp_val += 2*struct[temp_val_1,1]

    return struct


def create_formula(struct):
    n = np.sum(struct[:,1])
    formula = np.full(2*n, 0)
    temp_val = 0
    for i in range(struct.shape[0]):
        temp = struct[i]
        formula[temp_val] = temp[0]
        temp_val += 2
        for j in range(temp[1]-1):
            if j < temp[3]:
                formula[temp_val] = 2
            else:
                formula[temp_val] = 3

            temp_val += 2

    return formula


def update_struct(struct, numerator_condition):
    if numerator_condition:
        for i in range(struct.shape[0]-1, -1, -1):
            if struct[i,3] > (struct[i,1]-1)//2:
                temp = np.where((struct[i:,0]==struct[i,0]) & (struct[i:,1]==struct[i,1]))[0] + i
                struct[temp,3] = struct[i,3] - 1
                temp_1 = np.max(temp) + 1
                struct[temp_1:,3] = struct[temp_1:,1] - 1
                return True

        return False
    else:
        for i in range(struct.shape[0]-1, -1, -1):
            if struct[i,3] > 0:
                temp = np.where((struct[i:,0]==struct[i,0]) & (struct[i:,1]==struct[i,1]))[0] + i
                struct[temp,3] = struct[i,3] - 1
                temp_1 = np.max(temp) + 1
                struct[temp_1:,3] = struct[temp_1:,1] - 1
                return True

        return False


@njit
def harmean(arr):
    denominator = 0.0
    for v in arr:
        if v <= 0:
            return 0.0

        denominator += 1.0/v

    return len(arr) / denominator


@njit
def measurement_method_2(indexes, values, profits, interest_rate, f_profit):
    thresholds = values[:-1][indexes[:-1] != -1]
    max_profit = f_profit
    for x in thresholds:
        temp_profit = 1.0
        for i in range(len(values)-1):
            if values[i] > x:
                temp_profit *= profits[i]
            else:
                temp_profit *= interest_rate

        geo_ = temp_profit**(1.0/(len(profits)-1))
        if geo_ > max_profit:
            max_profit = geo_

    return max_profit


@njit
def measurement_method_3(indexes, values, profits, interest_rate, f_profit):
    thresholds = values[:-1][indexes[:-1] != -1]
    max_profit = f_profit
    for x in thresholds:
        temp_denomirator = 0.0
        for i in range(len(values)-1):
            if values[i] > x:
                temp_denomirator += 1.0/profits[i]
            else:
                temp_denomirator += 1.0/interest_rate

        har_ = (len(profits)-1) / temp_denomirator
        if har_ > max_profit:
            max_profit = har_

    return max_profit


@njit
def _countTrueFalse(a, b):
    countTrue = 0
    countFalse = 0
    len_ = len(a)
    for i in range(len_ - 1):
        for j in range(i+1, len_):
            if a[i] == a[j] and b[i] == b[j]:
                countTrue += 1
            else:
                if (a[i] - a[j]) * (b[i] - b[j]) > 0:
                    countTrue += 1
                else:
                    countFalse += 1

    return countTrue, countFalse


@njit
def countTrueFalse(a, b, index):
    countTrue = 0
    countFalse = 0
    for i in range(1, index.shape[0] - 1):
        t, f = _countTrueFalse(a[index[i]:index[i+1]], b[index[i]:index[i+1]])
        countTrue += t
        countFalse += f

    return countTrue / (countFalse + 1e-6)


@njit
def calculate_formula(formula, operand):
    temp_0 = np.zeros(operand.shape[1])
    temp_1 = temp_0.copy()
    temp_op = -1
    for i in range(1, formula.shape[0], 2):
        if formula[i] >= operand.shape[0]:
            raise

        if formula[i-1] < 2:
            temp_op = formula[i-1]
            temp_1 = operand[formula[i]].copy()
        else:
            if formula[i-1] == 2:
                temp_1 *= operand[formula[i]]
            else:
                temp_1 /= operand[formula[i]]

        if i+1 == formula.shape[0] or formula[i+1] < 2:
            if temp_op == 0:
                temp_0 += temp_1
            else:
                temp_0 -= temp_1

    temp_0[np.isnan(temp_0)] = -1.7976931348623157e+308
    temp_0[np.isinf(temp_0)] = -1.7976931348623157e+308
    return temp_0


@njit
def check_similar(INDEX, target, w1, w2):
    y = 0.0
    x = 0.0

    for i in range(INDEX.shape[0] - 1):
        a1 = np.argsort(np.argsort(w1[INDEX[i]: INDEX[i+1]]))
        a2 = np.argsort(np.argsort(w2[INDEX[i]: INDEX[i+1]]))
        a1 = (a1 + 1) / (len(a1))
        a2 = (a2 + 1) / (len(a2))

        y += 1 / len(a1) * np.corrcoef(a1, a2)[0, 1]
        x += 1 / len(a1)

    corrcoef = y / x
    if corrcoef <= target:
        return False

    return True


@njit
def correlation_filter(list_ct, OPERAND, INDEX, target, num_CT):
    list_index = List([0])
    list_weight = List([calculate_formula(list_ct[0], OPERAND)])
    count = 1
    for i in range(1, len(list_ct)):
        check = True
        weight = calculate_formula(list_ct[i], OPERAND)
        for w_j in list_weight:
            if check_similar(INDEX, target, weight, w_j):
                check = False
                break

        if check:
            list_index.append(i)
            list_weight.append(weight)
            count += 1
            if count == num_CT:
                print(i)
                break

    return list_index


@njit
def check_similar_2(f1_, f2_):
    f1 = np.unique(f1_[1::2])
    f2 = np.unique(f2_[1::2])

    if len(f1) > len(f2):
        F1 = f1
        F2 = f2
    else:
        F1 = f2
        F2 = f1

    count = 0
    for i in F1:
        if i not in F2:
            count += 1

    if count >= 2:
        return False

    return True


@njit
def similarity_filter(list_ct, num_CT):
    list_index = [0]
    count = 1
    for i in range(1, len(list_ct)):
        check = True
        for j in list_index:
            if check_similar_2(list_ct[i], list_ct[j]):
                check = False
                break

        if check:
            list_index.append(i)
            count += 1
            if count == num_CT:
                print(i)
                break

    return list_index
