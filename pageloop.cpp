#include <cassert>
#include <fstream>
#include <iostream>
#include <vector>
#include <utility>
#include <algorithm>
#include <queue>
#include <stack>
using namespace std;

ifstream in("input.txt");
ofstream out("output.txt");

int N, M, S, K;

struct nodo{
  vector<int> vic;
  int dist;
  bool active;

  nodo(){
    dist=-1;
    active=true;
  }
};

vector<nodo> grafo;
vector<nodo> grafoT;

void print_grafo() {
  for(int i=0; i<N; i++) {
    if(grafo[i].active) {
      for(int v:grafo[i].vic) {
        printf("%d -> %d\n", i, v);
      }
    }
  }
}

void bfs(int source){
  for(nodo& n:grafo)
    n.dist = -1;

  grafo[source].dist = 0;

  queue<int> q;
  q.push(source);
  int cur;
  while(!q.empty()){
    cur = q.front();
    q.pop();

    for(int v:grafo[cur].vic) {
      if((grafo[v].dist==-1) and (grafo[v].active)) {

        //Se un vicino non é ancora stato visitato, imposto la sua distanza.
        grafo[v].dist=grafo[cur].dist+1;
        q.push(v);
      }
    }

  }
}

int main(void) {
  in >> N >> M >> S >> K;

  grafo.resize(N);
  grafoT.resize(N);

  vector<bool> destroy(N, false);

  for(int i=0; i<M; i++) {
    int s, t;
    in >> s >> t;
    grafo[s].vic.push_back(t);
  }

  print_grafo();

  bfs(S);

  for(int i=0; i<N; i++) {
    printf("d(%d,%d) = %d\n", i, S, grafo[i].dist);

    if(grafo[i].dist > K) {
      destroy[i] = true;
    }
  }

  for(int i=0; i<N; i++) {
    printf("destroy[%d] = %s\n", i, destroy[i] ? "true" : "false");
    if(destroy[i]) {
      grafo[i].active = false;
      grafo[i].vic.clear();
    } else {
      for(int j=0; j<grafo[i].vic.size(); j++) {
        int v = grafo[i].vic[j];
        if(destroy[v]) {
          grafo[i].vic.erase(grafo[i].vic.begin()+j);
        }
      }
    }
  }

  N = grafo.size();
  print_grafo();

  return 0;
}
