#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Exemple d'utilisation de msocket et simpleroute, ensemble.
Agrège les réseaux connus d'un bloc et les envoie périodiquement.
"""
from msocket import msocket
from socket import gethostname
from select import select
from simpleroute import *
from time import time

mgrp="239.0.0.54"
mport=5454
tempo=10
bloc="10.0.0.0/8"

# récupère le nom du routeur et les réseaux auxquels il est connecté
host=gethostname()
conet=[(net,eif) for (net,gw,eif) in getroutes() if gw is None]

# crée une msocket pour chaque réseau connecté et initialise mmap avec les réseaux de [bloc]
mmap={}
msock=[]
for (net, eif) in conet:
    mip=getaddr(eif)
    mmap[net]= (0, None)
    print((net,eif,mip))
    if addrinnet(mip,bloc):
        ms=msocket(mgrp, mport, mip, eif)
        ms.ifname=eif
        msock.append(ms)

# fonctions de lecture/écriture de la mmap
def mastr(v):
	
    l=[]
    for (net, cost) in v:
      l.append("%s: %s" % (net, cost))
    return "\n".join(l)

def maparse(s, src):
    ss=s.strip().split("\n")
    print("Parsing '%s'" % (ss[0],))
    for l in ss[1:]:
        [net,cost]=l.strip().split(": ")
        cost = int(cost)
        if net in mmap:
            if cost+1 < mmap[net][0] or mmap[net][1] == src :
                mmap[net]=(cost+1, src)
                setroute(net, src)
        else:
            mmap[net]=(cost+1, src)
            setroute(net, src)

def printmmap():
	print(mmap)

# message de bienvenue
print("Bonjour, j'ai %d interfaces et ma map courante est :" % (len(msock),))
printmmap()

# emission vers dst
def emit(dst):
  v = []
  for net in mmap:
    if mmap[net][1] != dst :
      v.append( (net, mmap[net][0]) )
    else:
      v.append( (net, 8) )
  s=mastr(v)
  print("Envoi vers %s" % (ms.ifname,))
  dst.msend("de %s vers %s\n" % (host,ms.ifname) + s)

# reception depuis src des données data
def receive(src, eif, data):
  print("Reçu des données de %s via %s" % (src,eif))
  maparse(data, src)

# toutes les ~[tempo] secondes, apelle [emite(dst)] sur toutes les sockets [dst] de [msock]
# lorsqu'un message arrive, appelle [receive(src,eif,data)]
alarme=time()
while True:
    delta=alarme-time()
    while delta >= 0.0:
        (rl,rw,rx)=select(msock,[],[],delta)
        for ms in rl:
            (data,qui)=ms.mrecv(32768)
            receive(qui[0], ms.ifname, data)
        delta=alarme-time()
        printmmap()
        print
    for ms in msock:
      	emit(ms)
    alarme=time()+tempo
