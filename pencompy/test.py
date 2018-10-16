from pencompy import pencompy
from time import sleep

def callback(a,b,c):
    print(a,b,c)

p = pencompy('192.168.2.55',4008,callback=callback)
for t in range(5):
    p.set(0,0, t%2 == 0)
    sleep(7.)
p.set(0,0,False)
p.close()

