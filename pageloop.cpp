#include <cassert>
#include <fstream>
#include <iostream>
#include <vector>
#include <utility>
#include <algorithm>
#include <queue>
#include <stack>
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
vector<bool> destroy(N, false);
vector<stack<int>> cycles;

stack<int> tarjan_st;
stack<int> cycles_st;

void print_grafo() {
  for(int i=0; i<N; i++) {
    if(grafo[i].active) {
      for(int v:grafo[i].vic) {
        printf("%d -> %d\n", i, v);
      }
    }
  }
}

void destroy_nodes() {

  for(int i=0; i<N; i++) {
    // printf("destroy[%d] = %s\n", i, destroy[i] ? "true" : "false");
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

}

void bfs(int source) {

  if(!grafo[source].active) {
    return;
  }

  for(nodo& n:grafo) {
    n.dist = -1;
  }

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
        grafo[v].dist = grafo[cur].dist + 1;
        q.push(v);
      }
    }
  }

}


void tarjan_dfs(int n) {

  if(!grafo[n].active) {
    return;
  }

  grafo[n].index = counter;
  grafo[n].low = counter;
  counter++;

  tarjan_st.push(n);
  grafo[n].instack = true;

  for(int v:grafo[n].vic) {
    if(grafo[v].active) {
      if(grafo[v].index == -1) {
        tarjan_dfs(v);
        grafo[n].low = min(grafo[n].low, grafo[v].low);
      } else if(grafo[v].instack) {
        grafo[n].low = min(grafo[n].low, grafo[v].index);
      }
    }
  }

  if(grafo[n].low == grafo[n].index) {
    int el;

    if(n == S) {
      for(int i=0; i<N; i++) {
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
    } while((el != n) and !(tarjan_st.empty()));
    printf("\n");

  }

  return;

}


void print_stack(stack<int> s) {
  printf("(print_stack) stack size: %d\n", (int) s.size());
  while (!s.empty()) {
    cout << s.top();
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

void find_cycles(int n) {

  if(!grafo[n].active) {
    return;
  }

  printf("  -> n: %d\n", n);
  printf("     - counter: %d\n", counter);
  grafo[n].index = counter;
  grafo[n].low = counter;
  counter++;

  cycles_st.push(n);
  grafo[n].instack = true;

  for(int v:grafo[n].vic) {
    if(v==S) {
      printf("back to S (%d)\n", v);
      print_stack(cycles_st);

      if(!cycles_st.empty()) {
        cycles.push_back(cycles_st);
        print_cycles();
      }

    } else {
      if(grafo[v].active) {
        if(grafo[v].index == -1) {
          find_cycles(v);
        }
        cycles_st.pop();
        print_stack(cycles_st);
      }
    }
  }

  return;
}


int main(void) {
  in >> N >> M >> S >> K;

  grafo.resize(N);

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

  printf("print tarjan_st:\n");
  print_stack(tarjan_st);
  printf("---\n");

  counter = 0;
  find_cycles(S);

  return 0;
}
