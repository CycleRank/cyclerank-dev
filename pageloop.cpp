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
  vector<int> vic;
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

vector<bool> destroy;
vector<stack<int>> cycles;

stack<int> tarjan_st;
int counter = 0;

stack<int> circuits_st;


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

  for(int w : grafo[v].vic) {
    // printf("  --> w: %d\n", w);
    if (w == S) {
      // print_circuit(circuits_st);
      cycles.push_back(circuits_st);
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
    for (int w: grafo[v].vic) {
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
  destroy.resize(N);

  for(int i=0; i<N; i++) {
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
    if((grafo[i].dist == -1) or (grafo[i].dist > K-1)) {
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

  print_grafo();
  printf("---\n");

  // tarjan stack is empty here and may be reused

  // printf("S: %d\n", S);
  circuit(S);

  print_cycles();
  printf("***\n");

  for (auto& c : cycles) {
    while (!c.empty()) {
      int el = c.top();
      c.pop();
    }
  }


  return 0;
}
