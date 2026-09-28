import math


def find_order(a,N):
    """Smallest r>0 such that a^r=1 (Mod N). Assumes gcd(a,N)==1."""
    x= a%N
    r=1
    while x!=1:
        x=(x*a)%N
        r+=1
    return r


def try_factor(N,a):
    g= math.gcd(a,N)
    if g!=1:
        return (g,N//g), "lucky: a shares a factor with N"
    
    r= find_order(a,N)
    if r%2!=0:
        return None, f"r={r} is odd"
    
    half= pow(a, r//2, N)
    if half== N-1:
        return None, f"r={r}, but a^(r/2) = -1 (mod N)"
    
    p= math.gcd(half-1, N)
    q= math.gcd(half+1, N)
    return(p,q), f"r={r}, a^(r/2)= {half}"


def run_all(N):
    print(f"-----N={N}-----")
    coprime_tried= 0
    coprime_ok= 0
    for a in range(2, N):
        factors, note= try_factor(N,a)
        if math.gcd(a,N)==1:
            coprime_tried+=1
            if factors:
                coprime_ok+=1
        status= "OK " if factors else "FAIL"
        print(f"a={a:2d} {status} {factors} ({note})")
    print(f"coprime a that worked: {coprime_ok}/{coprime_tried}\n")
    
    
if __name__== "__main__":
    for N in (15,21,35,9,8):
        run_all(N)