bac = 1000
vir = 1
count = 0
ot = vir / bac
while bac:
    bac -= vir
    bac *= 2
    vir *= 2
    count += 1
    if ot < vir / bac:
        print(count)
    ot = vir  / bac
    print(bac, vir)
print(count)