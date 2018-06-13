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
  vector<int> vic;
  int dist;
  bool active;
  int index; // indice della dfs
  int low;   // piu basso indice utilizzando al massimo un back edge
  bool instack;

  nodo(){
    dist = -1;
    active = true;
    index = -1;
    instack = false;
    low = INT_MAX;
  }
};

vector<nodo> grafo;
int counter = 0;
vector<bool> destroy;
vector<stack<int>> cycles;

stack<int> tarjan_st;

stack<int> circuits_st;
vector<bool> blocked;

vector<list<int>> B;

void print_grafo() {
  for (int i=0; i<N; i++) {
    if (grafo[i].active) {
      for (int v:grafo[i].vic) {
        printf("%d -> %d\n", i, v);
      }
    }
  }
}

void destroy_nodes() {

  for(int i=0; i<N; i++) {
    // printf("destroy[%d] = %s\n", i, destroy[i] ? "true" : "false");
    if (destroy[i]) {
      grafo[i].active = false;
      grafo[i].vic.clear();
    } else {
      for (int j=0; j<grafo[i].vic.size(); j++) {
        int v = grafo[i].vic[j];
        if (destroy[v]) {
          grafo[i].vic.erase(grafo[i].vic.begin()+j);
        }
      }
    }
  }

}

void bfs(int source) {

  if (!grafo[source].active) {
    return;
  }

  for (nodo& n:grafo) {
    n.dist = -1;
  }

  grafo[source].dist = 0;

  queue<int> q;
  q.push(source);
  int cur;
  while (!q.empty()){
    cur = q.front();
    q.pop();

    for (int v:grafo[cur].vic) {
      if ((grafo[v].dist==-1) and (grafo[v].active)) {

        //Se un vicino non é ancora stato visitato, imposto la sua distanza.
        grafo[v].dist = grafo[cur].dist + 1;
        q.push(v);
      }
    }
  }

}


void tarjan_dfs(int n) {

  if (!grafo[n].active) {
    return;
  }

  grafo[n].index = counter;
  grafo[n].low = counter;
  counter++;

  tarjan_st.push(n);
  grafo[n].instack = true;

  for(int v:grafo[n].vic) {
    if (grafo[v].active) {
      if (grafo[v].index == -1) {
        tarjan_dfs(v);
        grafo[n].low = min(grafo[n].low, grafo[v].low);
      } else if (grafo[v].instack) {
        grafo[n].low = min(grafo[n].low, grafo[v].index);
      }
    }
  }

  if(grafo[n].low == grafo[n].index) {
    int el;

    if (n == S) {
      for (int i=0; i<N; i++) {
        if(!grafo[i].instack) {
          destroy[i] = true;
        }
      }
    }

    // trovato una componente fortemente connessa
    printf("SCC: ");
    do {
      el = tarjan_st.top();
      tarjan_st.pop();
      grafo[el].instack = false;
      printf("%d ", el);
    } while ((el != n) and !(tarjan_st.empty()));
    printf("\n");

  }

  return;
}


void print_stack(stack<int> s) {
  printf("(print_stack) stack size: %d\n", (int) s.size());
  while (!s.empty()) {
    printf("%d", s.top());
    s.pop();
  }
  printf("\n--- (print_stack) ---\n");
}


void print_cycles() {
  printf("***\n");
  printf("(print_cycles) cycles vector size: %d\n", (int) cycles.size());
  for (auto& st : cycles) {
    print_stack(st);
  }
  printf("\n--- (print_cycles) ---\n");
  printf("***\n");
}


void unblock(int u) {
  // printf("      ----> unblock(%d)\n", u);
  blocked[u] = false;
  // printf("        ----> blocked[%d]: %s\n", u, blocked[u] ? "true" : "false");

  while (!B[u].empty()) {
    int w = B[u].front();
    B[u].pop_front();

    if (blocked[w]) {
      unblock(w);
    }
  }
}


void output(stack<int> s) {
  vector<int> tmp;

  printf("      ----> found: ");
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


bool circuit(int v) {
  // printf("  --> circuit(%d)\n", v);

  bool flag = false;

  circuits_st.push(v);

  blocked[v] = true;
  // printf("  --> blocked[%d]: %s\n", v, blocked[v] ? "true" : "false");

  for(int w : grafo[v].vic) {
    // printf("  --> w: %d\n", w);
    if (w == S) {
      output(circuits_st);
      flag = true;
    } else if (!blocked[w]) {
      // printf("    ==> circuit(%d)\n", w);
      if (circuit(w)) {
        flag = true;
      }
    }
  }

  if (flag) {
    unblock(v);
  } else {
    for (int w: grafo[v].vic) {
      // printf("  ++> v: %d, w: %d\n", v, w);
      auto it = find(B[w].begin(), B[w].end(), v);
      // v not in B[w]
      if (it == B[w].end()) {
        // printf("  ++--> B[%d].push_back(%d)\n", w, v);
        B[w].push_back(v);
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
  destroy.resize(N);
  blocked.resize(N);
  B.resize(N);

  for(int i=0; i<M; i++) {
    destroy[i] = false;
  }

  for(int i=0; i<M; i++) {
    int s, t;
    in >> s >> t;
    grafo[s].vic.push_back(t);
  }

  print_grafo();
  printf("---\n");

  bfs(S);

  for(int i=0; i<N; i++) {
    // printf("d(%d,%d) = %d\n", i, S, grafo[i].dist);

    // se il nodo si trova distanza maggiore di K-1 o non raggiungibile
    if((grafo[i].dist > K-1) or (grafo[i].dist == -1)) {
      destroy[i] = true;
    }
  }

  destroy_nodes();

  print_grafo();
  printf("---\n");

  for(int i=0; i<N; i++) {
    destroy[i] = false;
  }

  tarjan_dfs(S);

  destroy_nodes();

  /*
  for(int i=0; i<N; i++) {
    printf("grafo[%d].active: %s - ", i, grafo[i].active ? "true" : "false");
    printf("grafo[%d].instack: %s\n", i, grafo[i].instack  ? "true" : "false");
  }
  */

  print_grafo();
  printf("---\n");

  for(int i=0; i<N; i++) {
    grafo[i].index = -1;
    grafo[i].low = INT_MAX;
    grafo[i].instack = false;
  }

  // tarjan stack is empty here and may be reused

  // printf("S: %d\n", S);
  for (int i=0; i<N; ++i) {
    blocked[i] = false;
    B[i].clear();
  }

  circuit(S);

  return 0;
}
