test = [0, 1, 2]
shuffle = [1, 2, 0]

for i in range(10):
    test = [test[idx] for idx in shuffle]
    print(test)