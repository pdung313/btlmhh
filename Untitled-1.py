import pulp
import numpy as np

# Kích thước tấm vật liệu lớn
W, H = 10, 10  # Chiều rộng và chiều cao của tấm lớn

# Danh sách các mảnh cần cắt (chiều rộng, chiều cao, số lượng yêu cầu)
pieces = [
    (2, 3, 5),  # mảnh có kích thước 2x3, cần 5 mảnh
    (3, 4, 3),  # mảnh có kích thước 3x4, cần 3 mảnh
    (5, 5, 2),  # mảnh có kích thước 5x5, cần 2 mảnh
]

# Khởi tạo tập mẫu cắt ban đầu (mỗi mẫu chứa một loại mảnh duy nhất)
initial_patterns = [[(i, pieces[i][2])] for i in range(len(pieces))]


def solve_master_problem(patterns, dual_prices=None):
    """
    Giải bài toán chính (master problem) bằng PuLP.
    """
    prob = pulp.LpProblem("CuttingStock", pulp.LpMinimize)
    
    # Biến số lần sử dụng mỗi mẫu cắt
    x_vars = [pulp.LpVariable(f"x_{i}", lowBound=0, cat="Integer") for i in range(len(patterns))]
    
    # Hàm mục tiêu: tổng số tấm lớn sử dụng
    prob += pulp.lpSum(x_vars)
    
    # Ràng buộc đáp ứng yêu cầu các mảnh
    for j, (w, h, demand) in enumerate(pieces):
        prob += pulp.lpSum(x_vars[i] * sum(1 for p in patterns[i] if p[0] == j) for i in range(len(patterns))) >= demand

    # Giải bài toán
    prob.solve()

    # Lấy nghiệm
    solution = [pulp.value(x) for x in x_vars]
    dual_prices = [c.pi for c in prob.constraints.values()]
    return solution, dual_prices


def solve_subproblem(dual_prices):
    """
    Giải bài toán con (Knapsack 2D) để tìm mẫu cắt mới.
    """
    # Bài toán con là Knapsack 2D để tìm mẫu cắt tối ưu.
    prob = pulp.LpProblem("Knapsack2D", pulp.LpMaximize)

    # Biến: số lần cắt mỗi mảnh
    y_vars = [pulp.LpVariable(f"y_{i}", lowBound=0, cat="Integer") for i in range(len(pieces))]

    # Hàm mục tiêu: tối ưu hóa giá trị giảm
    prob += pulp.lpSum(dual_prices[i] * y_vars[i] for i in range(len(pieces)))

    # Ràng buộc diện tích không vượt quá tấm lớn
    prob += pulp.lpSum(y_vars[i] * pieces[i][0] * pieces[i][1] for i in range(len(pieces))) <= W * H

    # Ràng buộc kích thước từng chiều
    for i in range(len(pieces)):
        prob += y_vars[i] * pieces[i][0] <= W  # Chiều rộng
        prob += y_vars[i] * pieces[i][1] <= H  # Chiều cao

    # Giải bài toán
    prob.solve()

    # Lấy mẫu cắt mới
    new_pattern = [(i, int(pulp.value(y_vars[i]))) for i in range(len(pieces)) if pulp.value(y_vars[i]) > 0]
    reduced_cost = pulp.value(prob.objective)
    return new_pattern, reduced_cost


def column_generation():
    """
    Thuật toán sinh cột để giải bài toán cắt vật liệu 2 chiều.
    """
    patterns = initial_patterns[:]
    while True:
        # Giải bài toán chính
        solution, dual_prices = solve_master_problem(patterns)

        # Giải bài toán con
        new_pattern, reduced_cost = solve_subproblem(dual_prices)

        # Nếu không còn mẫu cắt cải thiện, dừng
        if reduced_cost <= 1e-6:
            break

        # Thêm mẫu cắt mới
        patterns.append(new_pattern)

    return patterns, solution


# Chạy thuật toán
final_patterns, usage = column_generation()

# Kết quả
print("Mẫu cắt cuối cùng:")
for i, pattern in enumerate(final_patterns):
    print(f"Mẫu {i + 1}: {pattern}, sử dụng {usage[i]} lần")

print("\nTổng số tấm lớn cần dùng:", sum(usage))
