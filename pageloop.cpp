#include <cassert>
#include <fstream>
#include <iostream>
#include <vector>
#include <utility>
#include <algorithm>
#include <stack>
using namespace std;

ifstream in("input.txt");
ofstream out("output.txt");

int N, M;

struct nodo{
  vector<int> vic;
  bool visited;
  nodo(){
    visited=false;
  }
};

vector<nodo> grafo;
vector<nodo> grafoT;

int counter=0;
stack<int> ordine;
void dfsG(int n){
  grafo[n].visited=true;
  for(int i=0; i<grafo[n].vic.size(); i++){
    int v=grafo[n].vic[i];
    if(!grafo[v].visited)
      dfsG(v);
  }
  ordine.push(n);
}

void dfsGT(int n){
  grafoT[n].visited=true;
  for(int i=0; i<grafoT[n].vic.size(); i++){
    int v=grafoT[n].vic[i];
    if(!grafoT[v].visited)
      dfsGT(v);
  }
  counter++;
}


int main(void)
{
  in >> N >> M;
  grafo.resize(N);
  grafoT.resize(N);

  for(int i=0; i<M; i++) {
    int s, t;
    in >> s >> t;
    grafo[s].vic.push_back(t);
    grafoT[t].vic.push_back(s);
  }

  for(int i = 0; i<N; i++){
    if(!grafo[i].visited){
      dfsG(i);
    }
  }

  int mx = -1;
  for(int j = N-1; j >= 0; j--) {
    int i=ordine.top();
    ordine.pop();
    
    if(!grafoT[i].visited) {
      counter=0;
      dfsGT(i);
      mx=max(mx,counter);
    }    
  }
  out<<mx<<endl;
  return 0;
}

