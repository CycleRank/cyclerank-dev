#include <cassert>
#include <fstream>
#include <iostream>
#include <vector>
#include <utility>
#include <algorithm>
#include <queue>
#include <stack>
#include <list>
#include <climits>
using namespace std;

ifstream in("input.txt");
ofstream out("output.txt");

int N, M, S, K;

struct nodo{
  bool active;
  bool instack;
  bool blocked;
  int dist;
  int index; // indice della dfs
  int low;   // piu basso indice utilizzando al massimo un back edge
  double score;
  vector<int> adj;
  list<int> B;

  nodo(){
    active = true;
    instack = false;
    blocked = false;
    dist = -1;
    index = -1;
    low = INT_MAX;
    score = 0.0;
    B.clear();
  }
};

vector<nodo> grafo;
vector<nodo> grafoT;

vector<bool> destroy;
vector<stack<int>> cycles;

stack<int> tarjan_st;
int counter = 0;

stack<int> circuits_st;


void print_g(vector<nodo>& g) {
  for (int i=0; i<N; i++) {
    if (g[i].active) {
      for (int v: g[i].adj) {
        printf("%d -> %d\n", i, v);
      }
    }
  }
}


void destroy_nodes(vector<nodo>& g) {

  for(int i=0; i<N; i++) {
    // printf("destroy[%d] = %s\n", i, destroy[i] ? "true" : "false");
    if (destroy[i]) {
      g[i].active = false;
      g[i].adj.clear();
    } else {
      for (int j=0; j<g[i].adj.size(); j++) {
        int v = g[i].adj[j];
        if (destroy[v]) {
          g[i].adj.erase(g[i].adj.begin()+j);
        }
      }
    }
  }
}


void bfs(int source, vector<nodo>& g) {

  if (!g[source].active) {
    return;
  }

  for (nodo& n: g) {
    n.dist = -1;
  }

  g[source].dist = 0;

  queue<int> q;
  q.push(source);
  int cur;
  while (!q.empty()){
    cur = q.front();
    q.pop();

    // if g[cur].dist == K-1 we can stop
    if(g[cur].dist > K-2) {
      continue;
    }

    for (int v: g[cur].adj) {
      if ((g[v].dist==-1) and (g[v].active)) {

        // neighbor not yet visited, set distance
        g[v].dist = g[cur].dist + 1;
        q.push(v);
      }
    }
  }
}


void print_stack(stack<int> s) {
  printf("(print_stack) stack size: %d\n", (int) s.size());
  while (!s.empty()) {
    printf("%d", s.top());
    s.pop();
  }
  printf("\n--- (print_stack) ---\n");
}


void print_circuit(stack<int> s) {
  vector<int> tmp;

  // printf("      ----> found: ");
  printf("--> cycle: ");
  while (!s.empty()) {
    int el = s.top();
    tmp.push_back(el);
    s.pop();
  }

  for (int j=tmp.size()-1; j>=0; j--) {
    printf("%d-", tmp[j]);
  }
  int last = tmp[tmp.size()-1];
  printf("%d\n", last);
}


void print_cycles() {
  for (auto& st : cycles) {
    print_circuit(st);
  }
}


void unblock(int u) {
  // printf("      ----> unblock(%d)\n", u);
  grafo[u].blocked = false;
  // printf("        ----> grafo[%d].blocked: %s\n", u, grafo[u].blocked ? "true" : "false");

  while (!grafo[u].B.empty()) {
    int w = grafo[u].B.front();
    grafo[u].B.pop_front();

    if (grafo[w].blocked) {
      unblock(w);
    }
  }
}


bool circuit(int v) {
  // printf("  --> circuit(%d)\n", v);

  bool flag = false;

  circuits_st.push(v);

  grafo[v].blocked = true;
  // printf("  --> grafo[%d].blocked: %s\n", v, grafo[v].blocked ? "true" : "false");

  for(int w : grafo[v].adj) {
    // printf("  --> w: %d\n", w);
    if (w == S) {
      // print_circuit(circuits_st);
      if (!(circuits_st.size() > K)) {
        cycles.push_back(circuits_st);
      }
      flag = true;
    } else if (!grafo[w].blocked) {
      // printf("    ==> circuit(%d)\n", w);
      if (circuit(w)) {
        flag = true;
      }
    }
  }

  if (flag) {
    unblock(v);
  } else {
    for (int w: grafo[v].adj) {
      // printf("  ++> v: %d, w: %d\n", v, w);
      auto it = find(grafo[w].B.begin(), grafo[w].B.end(), v);
      // v not in B[w]
      if (it == grafo[w].B.end()) {
        // printf("  ++--> B[%d].push_back(%d)\n", w, v);
        grafo[w].B.push_back(v);
      }
    }
  }

  circuits_st.pop();

  // printf("<-- v: %d\n", v);
  return flag;
}


int main(void) {
  in >> N >> M >> S >> K;

  grafo.resize(N);
  grafoT.resize(N);
  destroy.resize(N);

  for(int i=0; i<N; i++) {
    destroy[i] = false;
  }

  for(int i=0; i<M; i++) {
    int s, t;
    in >> s >> t;
    grafo[s].adj.push_back(t);
    grafoT[t].adj.push_back(s);
  }

  print_g(grafo);
  printf("---\n");
  print_g(grafoT);
  printf("***\n");

  bfs(S, grafo);

  for(int i=0; i<N; i++) {
    // printf("d(%d,%d) = %d\n", i, S, grafo[i].dist);

    // se il nodo si trova distanza maggiore di K-1 o non raggiungibile
    if((grafo[i].dist == -1) or (grafo[i].dist > K-1)) {
      destroy[i] = true;
    }
  }

  destroy_nodes(grafo);
  destroy_nodes(grafoT);

  bfs(S, grafoT);

  for(int i=0; i<N; i++) {
    printf("grafo[%d].dist: %d\n", i, grafo[i].dist);
  }
  printf("---\n");

  for(int i=0; i<N; i++) {
    printf("grafoT[%d].dist: %d\n", i, grafoT[i].dist);
  }
  printf("***\n");

  for(int i=0; i<N; i++) {
    // printf("d(%d,%d) = %d\n", i, S, grafo[i].dist);

    // se il nodo si trova distanza maggiore di K-1 o non raggiungibile
    if((grafo[i].dist == -1) or (grafoT[i].dist == -1) or (grafo[i].dist + grafoT[i].dist > K)) {
      destroy[i] = true;
    }
  }

  destroy_nodes(grafo);

  print_g(grafo);
  printf("---\n");

  // printf("S: %d\n", S);
  circuit(S);

  print_cycles();
  printf("***\n");

  for (auto& c : cycles) {
    int csize = c.size();
    print_circuit(c);
    while (!c.empty()) {
      int el = c.top();
      c.pop();

      printf("%d <- %f\n", el, 1.0/csize);

      grafo[el].score += 1.0/csize;
    }
  }

  printf("---\n");
  for (int i=0; i<N; i++) {
    printf("score(%d): %f\n", i, grafo[i].score);
  }

  return 0;
}
