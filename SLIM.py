import numpy as np
from os import urandom

def WORD_SIZE():
    return(16);

def ALPHA():
    return(7);

def BETA():
    return(2);

MASK_VAL = 2 ** WORD_SIZE() - 1;

P_r =   [8,14,2,9,12,15,3,6,5,11,16,1,4,7,10,13];
P =     [12,3,7,13,9,8,14,1,4,15,10,5,16,2,6,11];

S =  [12,5,6,11,9,0,10,13,3,14,15,8,4,7,1,2];


def shuffle_together(l):
    state = np.random.get_state();
    for x in l:
        np.random.set_state(state);
        np.random.shuffle(x);

def rol(x,k):
    return(((x << k) & MASK_VAL) | (x >> (WORD_SIZE() - k)));

def rol40(x,k):
    mask = 2 ** 40 - 1;
    return(((x << k) & mask) | (x >> (40 - k)));

def rolnib(x,k):
    mask = 2 ** 4 - 1;
    return(((x << k) & mask) | (x >> (4 - k)));

def ror(x,k):
    return((x >> k) | ((x << (WORD_SIZE() - k)) & MASK_VAL));

#def enc_one_round(p, k):
#    c0, c1 = p[0], p[1];
#    c0 = ror(c0, ALPHA());
#    c0 = (c0 + c1) & MASK_VAL;
#    c0 = c0 ^ k;
#    c1 = rol(c1, BETA());
#    c1 = c1 ^ c0;
#    return(c0,c1);

def enc_one_round(p,k):
    l,r =  p[0], p[1];
    r_temp = r;

    #original#
    r_k = (r_temp ^ k) ;
    r_s = substitute(r_k,S);
    
    #swapped#
    #r_temp = r_temp+0;
    #r_temp = substitute(r_temp,S);
    #r_temp = (r_temp ^ k) ;

    r_p = permute(r_s, P);
    l_temp = (l^r_p) ;
    l = r;
    r = l_temp;
  
    return(l,r);

def dec_one_round(c,k):
    l,r =  c[0], c[1];
    l_temp = l;
    
    #original#
    l_temp = (l_temp ^ k) ;
    l_temp = substitute(l_temp,S);

    #swapped#
    #l_temp = substitute(l_temp,S);
    #l_temp = (l_temp ^ k) ;

    l_temp = permute(l_temp, P);
    r_temp = (r^l_temp) ;
    r = l;
    l = r_temp;
  
    r=c[0];
    l=c[1];

    return(l,r);

def enc_one_round_LBC(p,k):
    l,r =  p[0], p[1];

    #P2
    r_p = permute(r,P2);
   
    #Left Shift   
    r = rol(r,7);

    #Substitution
    r_s = substitute (r,S);

    #Modular Addition
    l= (l+r_s+k) & MASK_VAL;

    #P1
    r = permute(l,P1);

    l=r_p;
    return(l,r);

#def dec_one_round(c,k):
#    c0, c1 = c[0], c[1];
#    c1 = c1 ^ c0;
#    c1 = ror(c1, BETA());
#    c0 = c0 ^ k;
#    c0 = (c0 - c1) & MASK_VAL;
#    c0 = rol(c0, ALPHA());
#    return(c0, c1);

#def expand_key(k, t):
#    ks = [0 for i in range(t)];
#    ks[0] = k[len(k)-1];
#    l = list(reversed(k[:len(k)-1]));
#    for i in range(t-1):
#        l[i%3], ks[i+1] = enc_one_round((l[i%3], ks[i]), i);
#    return(ks);

#SLIM Key Schedule
def expand_key(k,t):
    ks = [0 for i in range(t)];
    
    L = (2**32)*np.uint64(k[2]&0xff)+(2**16)*np.uint64(k[3])+np.uint64(k[4]);
    M = (2**24)*np.uint64(k[0])+(2**8)*np.uint64(k[1])+np.uint64(k[2]>>8);
     
    for i in range(t):
        if i<5:
          ks[i]=k[4-i];
        else:
          Lnib = np.zeros((4,int(k.size/5)),dtype=np.int16);
          Mnib = np.zeros((4,int(k.size/5)),dtype=np.int16);

          Lnib[0] = np.uint16(L&0xf);
          Lnib[1] = np.uint16((L>>4)&0xf);
          Lnib[2] = np.uint16((L>>8)&0xf);
          Lnib[3] = np.uint16((L>>12)&0xf);

          Mnib[0] = np.uint16((M)&0xf);
          Mnib[1] = np.uint16((M>>4)&0xf);
          Mnib[2] = np.uint16((M>>8)&0xf);
          Mnib[3] = np.uint16((M>>12)&0xf);

          Lnib = rolnib(Lnib,2);

          Lnib = Lnib^Mnib;

          for j_1 in range(0,Lnib.shape[0]):
            for j_2 in range(0,Lnib.shape[1]):
              Lnib[j_1][j_2]=S[Lnib[j_1][j_2]];

          Mnib = rolnib(Mnib,3);

          Mnib = Mnib^Lnib;

          L_16 = Lnib[0] + Lnib[1]*(2**4) + Lnib[2]*(2**8) + np.uint16(Lnib[3])*(2**12);
          M_16 = Mnib[0] + Mnib[1]*(2**4) + Mnib[2]*(2**8) + np.uint16(Mnib[3])*(2**12);

          M = np.uint64(M>>16) + np.uint64(M_16)*(2**24);
          L = np.uint64(L>>16) + np.uint64(L_16)*(2**24);

          ks[i] = M_16;

         
    return(ks);

def expand_key_LBC(k,t):
    ks = [0 for i in range(t)];
    
    L = (2**32)*np.uint64(k[2]&0xff)+(2**16)*np.uint64(k[3])+np.uint64(k[4]);
    M = (2**24)*np.uint64(k[0])+(2**8)*np.uint64(k[1])+np.uint64(k[2]>>8);
     
    for i in range(t):
        if i<5:
          ks[i]=k[4-i];
        else:
          Lnib = np.zeros((4,int(k.size/5)),dtype=np.int16);
          Mnib = np.zeros((4,int(k.size/5)),dtype=np.int16);

          Lnib[0] = np.uint16(L&0xf);
          Lnib[1] = np.uint16((L>>4)&0xf);
          Lnib[2] = np.uint16((L>>8)&0xf);
          Lnib[3] = np.uint16((L>>12)&0xf);

          Mnib[0] = np.uint16((M)&0xf);
          Mnib[1] = np.uint16((M>>4)&0xf);
          Mnib[2] = np.uint16((M>>8)&0xf);
          Mnib[3] = np.uint16((M>>12)&0xf);

          Lnib = rolnib(Lnib,3);

          Lnib = Lnib^Mnib;

          for i in range(0,Lnib.shape[0]):
            for j in range(0,Lnib.shape[1]):
              Lnib[i][j]=S1[Lnib[i][j]];

          M_16 = Mnib[0] + Mnib[1]*(2**4) + Mnib[2]*(2**8) + np.uint16(Mnib[3])*(2**12);
          M_16 = permute(M_16,P1);

          Mnib[0] = np.uint16((M_16)&0xf);
          Mnib[1] = np.uint16((M_16>>4)&0xf);
          Mnib[2] = np.uint16((M_16>>8)&0xf);
          Mnib[3] = np.uint16((M_16>>12)&0xf);

          Mnib = Mnib^Lnib;

          L_16 = Lnib[0] + Lnib[1]*(2**4) + Lnib[2]*(2**8) + np.uint16(Lnib[3])*(2**12);
          M_16 = Mnib[0] + Mnib[1]*(2**4) + Mnib[2]*(2**8) + np.uint16(Mnib[3])*(2**12);

          M = np.uint64(M>>16) + np.uint64(M_16)*(2**24);
          L = np.uint64(L>>16) + np.uint64(L_16)*(2**24);

          ks[i] = M_16;
    return(ks);

def substitute (x , s):
    y = x*0;
    for i in range(0,x.size):
      y[i] += s[(x[i]%16)]; 
      x[i]=x[i]>>4;
      y[i] += (s[x[i]%16]<<4);
      x[i]=x[i]>>4;
      y[i] += (s[x[i]%16]<<8);
      x[i]=x[i]>>4;
      y[i] += (s[x[i]%16]<<12);

    return y;


def permute(x,p):
    y = x*0;
    for i in range(0,16):
      y+=(x%2)*(2**(16-p[15-i]));
      x=x>>1;
    return y;


def encrypt(p, ks):
    x, y = p[0], p[1];
    i = 1;
    for k in ks:

        x,y = enc_one_round((x,y), k);
        
        i=i+1;

    return(x, y);

def decrypt(c, ks):
    x, y = c[0], c[1];
    i = 1;
    for k in reversed(ks):

        x,y = dec_one_round((x,y), k);
        
        i=i+1;

    return(x, y);

#Original
#def decrypt(c, ks):
#    x, y = c[0], c[1];
#    for k in reversed(ks):
#        x, y = dec_one_round((x,y), k);
#    return(x,y);

def check_testvector():
  key = (0x1918,0x1110,0x0908,0x0100)
  pt = (0x6574, 0x694c)
  ks = expand_key(key, 22)
  ct = encrypt(pt, ks)
  if (ct == (0xa868, 0x42f2)):
    print("Testvector verified.")
    return(True);
  else:
    print("Testvector not verified.")
    return(False);

#convert_to_binary takes as input an array of ciphertext pairs
#where the first row of the array contains the lefthand side of the ciphertexts,
#the second row contains the righthand side of the ciphertexts,
#the third row contains the lefthand side of the second ciphertexts,
#and so on
#it returns an array of bit vectors containing the same data
def convert_to_binary(arr):
  X = np.zeros((4 * WORD_SIZE(),len(arr[0])),dtype=np.uint8);
  for i in range(4 * WORD_SIZE()):
    index = i // WORD_SIZE();
    offset = WORD_SIZE() - (i % WORD_SIZE()) - 1;
    X[i] = (arr[index] >> offset) & 1;
  X = X.transpose();
  return(X);

#takes a text file that contains encrypted block0, block1, true diff prob, real or random
#data samples are line separated, the above items whitespace-separated
#returns train data, ground truth, optimal ddt prediction
def readcsv(datei):
    data = np.genfromtxt(datei, delimiter=' ', converters={x: lambda s: int(s,16) for x in range(2)});
    X0 = [data[i][0] for i in range(len(data))];
    X1 = [data[i][1] for i in range(len(data))];
    Y = [data[i][3] for i in range(len(data))];
    Z = [data[i][2] for i in range(len(data))];
    ct0a = [X0[i] >> 16 for i in range(len(data))];
    ct1a = [X0[i] & MASK_VAL for i in range(len(data))];
    ct0b = [X1[i] >> 16 for i in range(len(data))];
    ct1b = [X1[i] & MASK_VAL for i in range(len(data))];
    ct0a = np.array(ct0a, dtype=np.uint16); ct1a = np.array(ct1a,dtype=np.uint16);
    ct0b = np.array(ct0b, dtype=np.uint16); ct1b = np.array(ct1b, dtype=np.uint16);
    
    #X = [[X0[i] >> 16, X0[i] & 0xffff, X1[i] >> 16, X1[i] & 0xffff] for i in range(len(data))];
    X = convert_to_binary([ct0a, ct1a, ct0b, ct1b]); 
    Y = np.array(Y, dtype=np.uint8); Z = np.array(Z);
    return(X,Y,Z);

#baseline training data generator
def make_train_data(n, nr, diff=(0x0040,0)):
  Y = np.frombuffer(urandom(n), dtype=np.uint8); Y = Y & 1;
  keys = np.frombuffer(urandom(10*n),dtype=np.uint16).reshape(5,-1);
  plain0l = np.frombuffer(urandom(2*n),dtype=np.uint16);
  plain0r = np.frombuffer(urandom(2*n),dtype=np.uint16);
  plain1l = plain0l ^ diff[0]; plain1r = plain0r ^ diff[1];
  num_rand_samples = np.sum(Y==0);
  plain1l[Y==0] = np.frombuffer(urandom(2*num_rand_samples),dtype=np.uint16);
  plain1r[Y==0] = np.frombuffer(urandom(2*num_rand_samples),dtype=np.uint16);
  ks = expand_key(keys, nr);
  ctdata0l, ctdata0r = encrypt((plain0l, plain0r), ks);
  ctdata1l, ctdata1r = encrypt((plain1l, plain1r), ks);
  X = convert_to_binary([ctdata0l, ctdata0r, ctdata1l, ctdata1r]);
  return(X,Y);

#real differences data generator
def real_differences_data(n, nr, diff=(0x0040,0)):
  #generate labels
  Y = np.frombuffer(urandom(n), dtype=np.uint8); Y = Y & 1;
  #generate keys
  keys = np.frombuffer(urandom(10*n),dtype=np.uint16).reshape(5,-1);
  #generate plaintexts
  plain0l = np.frombuffer(urandom(2*n),dtype=np.uint16);
  plain0r = np.frombuffer(urandom(2*n),dtype=np.uint16);
  #apply input difference
  plain1l = plain0l ^ diff[0]; plain1r = plain0r ^ diff[1];
  num_rand_samples = np.sum(Y==0);
  #expand keys and encrypt
  ks = expand_key(keys, nr);
  ctdata0l, ctdata0r = encrypt((plain0l, plain0r), ks);
  ctdata1l, ctdata1r = encrypt((plain1l, plain1r), ks);
  #generate blinding values
  k0 = np.frombuffer(urandom(2*num_rand_samples),dtype=np.uint16);
  k1 = np.frombuffer(urandom(2*num_rand_samples),dtype=np.uint16);
  #apply blinding to the samples labelled as random
  ctdata0l[Y==0] = ctdata0l[Y==0] ^ k0; ctdata0r[Y==0] = ctdata0r[Y==0] ^ k1;
  ctdata1l[Y==0] = ctdata1l[Y==0] ^ k0; ctdata1r[Y==0] = ctdata1r[Y==0] ^ k1;
  #convert to input data for neural networks
  X = convert_to_binary([ctdata0l, ctdata0r, ctdata1l, ctdata1r]);
  return(X,Y);
