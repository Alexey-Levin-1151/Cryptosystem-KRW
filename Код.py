import sage
from sage.all import *
import itertools
from itertools import product
from itertools import combinations
import sys
print(sys.version)

print(sage.version.version)
def random_invertible_matrix(n, field=GF(2)): #Создает случайную обратимую матрицу размера n x n над заданным полем.
    # Создаем случайную матрицу над заданным полем
    A = matrix(field, n, n, [field.random_element() for _ in range(n**2)])
    # Проверяем, является ли матрица обратимой
    if A.is_invertible():
        return A
    else:
        # Если матрица не обратима, пробуем снова
        return random_invertible_matrix(n, field)
    
def weight(v):
    return sum(v)

# Функция для вычисления веса вектора
def hamming_weight(v):
    return sum(1 for x in v if x != 0)

def Cryptosystem(param_for_crypt):
    m,la,q,n,k = param_for_crypt
    F = GF(q^m)
    #Создание поля и кода GRS
    gamma = F.primitive_element() # Примитивный элемент поля
    C = codes.GeneralizedReedSolomonCode(F.list()[:n], k)
    E = codes.encoders.GRSEvaluationVectorEncoder(C)
    G = E.generator_matrix()
    H = C.parity_check_matrix()
    D = codes.decoders.GRSBerlekampWelchDecoder(C)
    show("decoding radius: ", D.decoding_radius())

    #Создание расширенной матрицы проверки на чётность
    Hexp = matrix(F,m*(n-k),m*n)
    jj = 0
    for j in range(0,n*m,m):
        for ii in range(m):
            for i in range(n-k):
                for ttt in range(m):
                    Hexp[m*i+ttt,j+ii] = list(H[i,jj]*gamma^ii)[ttt]
        jj = jj+1

    #Прокалывание в S столбцах
    S = matrix(m-la,n)
    for j in range(n):
        vec = []
        for i in range(m-la):
            if i == 0:
                S[i,j] = randint(0, m-1)
                vec.append(S[i,j])
            else:
                S[i,j] = randint(0, m-1)
                while S[i,j] in vec:
                    S[i,j] = randint(0, m-1)
                vec.append(S[i,j])
    HexpS = matrix(GF(q), m*(n-k),la*n)
    count = 0
    count2 = 0 
    for j in range(n):
        vec = []
        for i in range(m-la):
            vec.append(S[i,j])
        for jj in range(m):
            if jj % m not in vec:
                for i in range(m*(n-k)):
                    HexpS[i,count] = Hexp[i,count2]
                count = count + 1
            count2 = count2 + 1

    #Создание блочной диагональный матрицы T
    A = []
    for i in range(n):
        A.append(random_invertible_matrix(la,GF(q)))
    T = block_diagonal_matrix(A)

    #Создание блочной матрицы перестановок P_sigma
    B = []
    perm = Permutations(n).random_element()
    for i in range(la):
        B.append(perm.to_matrix())
    P = block_diagonal_matrix(B)

    Q = T * P
    HH = HexpS * Q
    
    Openkey = [HH, D.decoding_radius(), la]
    Privkey = [H, Q, gamma, S]
    return Openkey, Privkey

def find_error_from_syndrome(H, s, param_for_crypt, F, max_weight=2):
    m,la,q,n,k = param_for_crypt
    n = H.ncols()
    e_return = []
    for t in range(1, max_weight + 1):
        for positions in Combinations(range(n), t):
            H_sub = H.matrix_from_columns(positions)
            try:
                x = H_sub.solve_right(s)
                e = matrix(F, n, 1)
                for i in range(n):
                    e[i,0] = 0
                for i, pos in enumerate(positions):
                    e[pos,0] = x.list()[i]
                d = H*e
                if d == s:
                    b = 0
                    for i in range(0,n):
                        if e[i,0] != 0:
                            b += 1
                    if b <= t:
                        e_return.append(e)
                    else:
                        continue
            except:
                continue
    if not e_return:
        raise ValueError("Решение не найдено")
    else:
        return e_return
    
def Encrypt(y, Openkey):
    HH = Openkey[0]
    t = Openkey[1]
    c = matrix(GF(q),m*(n-k),1)
    c = HH*y.transpose()
    show("c = ", c.transpose())
    return c

def Decrypt(c, Privkey, Openkey, param_for_crypt):
    t = Openkey[1]
    H, Q, gamma, S = Privkey
    m,la,q,n,k = param_for_crypt
    F = GF(q^m)
    #Сокращение сс
    cc = matrix(F,n-k, 1)
    for i in range(0,n-k):
        x = 0
        for j in range(m):
            x = x + c[m*i+j,0]*gamma^j
        cc[i,0] = x
    
    good_answers = find_error_from_syndrome(H, cc, param_for_crypt, F, 2*t)  # Ищем ошибку веса ≤ t
    
    Q_inv = Q.inverse()
    a=0
    good_answers2 = []
    for best_solution in good_answers:

        #Применение фи_n к результату
        HHHHH = matrix(F,1,m*n)
        jj = 0
        for j in range(0,n):
            for ttt in range(m):
                HHHHH[0,m*j+ttt] = list(best_solution[j,0])[ttt]

        #Прокалывание в S столбцах
        yy = matrix(F,1,la*n)
        count = 0
        count2 = 0 
        for j in range(n):
            vec = []
            for i in range(m-la):
                vec.append(S[i,j])
            for jj in range(m):
                if jj not in vec:
                    yy[0,count] = HHHHH[0,count2]
                    count = count + 1
                count2 = count2 + 1

        #Умножение на Q^-1
        yyy = Q_inv*yy.transpose()
        #Проверка, что в S позициях стоят нули
        b=0
        for j in range(n):
            vec = []
            for i in range(m-la):
                vec.append(S[i,j])
            for jj in range(m):
                if jj in vec:
                    if HHHHH[0,m*j+jj] != 0:
                        b=1
        #Проверка, что вес сообщения <=t*la
        c=0
        for i in range(0,la*n,la):
            if yyy[i,0] == 1 or yyy[i+1,0] == 1:
                c += 1
        if b == 0 and c <=t :
            if yyy not in good_answers2:
                good_answers2.append(yyy)
        else:
            a=a+1
    if not good_answers2:
        show("There is no solution")
    else:
        show("Possible answers: ")
        for good in good_answers2:
            show("y'= ",good.transpose())
        

#Задаём криптосистему
m=3
la=2
q=2
n=8
k=4
param_for_crypt = [m,la,q,n,k]
Openkey, Privkey = Cryptosystem(param_for_crypt)

#Шифрование
MMDD = MatrixSpace(GF(q),1,la*n)
y = MMDD([0,0,0,0,1,1,0,0,0,0,1,1,0,0,0,0]) #Задаём сообщение
show("y = ", y)
c = matrix(GF(q),m*(n-k),1)
c = Encrypt(y, Openkey)

#Расшифровка
Decrypt(c, Privkey, Openkey, param_for_crypt)
    