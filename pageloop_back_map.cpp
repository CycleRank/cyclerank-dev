#include <cassert>
#include <fstream>
#include <iostream>
#include <vector>
#include <utility>
#include <algorithm>
#include <queue>
#include <stack>
#include <list>
#include <map>
#include <climits>

#include "spdlog/spdlog.h"

using namespace std;
namespace spd = spdlog;

ifstream in("input.txt");
ofstream out("output.txt");

int N, M, S, K;

struct nodo{
  bool active;
  bool instack;
  bool blocked;
  int dist;
  int index;
  int low;
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
  for (int i=0; i<g.size(); i++) {
    if (g[i].active) {
      for (int v: g[i].adj) {
        printf("%d -> %d\n", i, v);
      }
    }
  }
}


void destroy_nodes(vector<nodo>& g) {

  for(int i=0; i<g.size(); i++) {
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
  bool flag = false;

  circuits_st.push(v);

  grafo[v].blocked = true;

  for(int w : grafo[v].adj) {
    if (w == S) {
      if (!(circuits_st.size() > K)) {
        cycles.push_back(circuits_st);
      }
      flag = true;
    } else if (!grafo[w].blocked) {
      if (circuit(w)) {
        flag = true;
      }
    }
  }

  if (flag) {
    unblock(v);
  } else {
    for (int w: grafo[v].adj) {
      auto it = find(grafo[w].B.begin(), grafo[w].B.end(), v);
      if (it == grafo[w].B.end()) {
        grafo[w].B.push_back(v);
      }
    }
  }

  circuits_st.pop();

  return flag;
}


int main(int argc, char* argv[]) {

  try {
    // Console logger with color
    auto console = spd::stdout_color_mt("console");
    console->info("Welcome to spdlog!");
    console->error("Some error message with arg{}..", 1);

    // Formatting examples
    console->warn("Easy padding in numbers like {:08d}", 12);
    console->critical("Support for int: {0:d};  hex: {0:x};  oct: {0:o}; bin: {0:b}", 42);
    console->info("Support for floats {:03.2f}", 1.23456);
    console->info("Positional args are {1} {0}..", "too", "supported");
    console->info("{:<30}", "left aligned");
  }
  // Exceptions will only be thrown upon failed logger or sink construction (not during logging)
  catch (const spd::spdlog_ex& ex) {
      std::cout << "Log init failed: " << ex.what() << std::endl;
      return 1;
  }

  exit(0);

  in >> N >> M >> S >> K;

  grafo.resize(N);
  destroy.resize(N);

  map<int,int> old2new;
  vector<int> new2old;

  for(int i=0; i<N; i++) {
    destroy[i] = false;
  }

  for(int i=0; i<M; i++) {
    int s, t;
    in >> s >> t;
    grafo[s].adj.push_back(t);
  }

  print_g(grafo);
  printf("---\n");

  bfs(S, grafo);

  int count_destroied = 0;
  for(int i=0; i<N; i++) {

    // se il nodo si trova distanza maggiore di K-1 o non raggiungibile
    if((grafo[i].dist == -1) or (grafo[i].dist > K-1)) {
      printf("destroied node: %d\n", i);
      destroy[i] = true;
      count_destroied++;
    }
  }

  int remaining = N-count_destroied;

  printf("-> nodes: %d\n", N);
  printf("-> destroyed: %d\n", count_destroied);
  printf("-> remaining: %d\n", remaining);

  new2old.resize(remaining);

  vector<nodo> tmpgrafo;
  tmpgrafo.resize(remaining);

  int newindex = -1;
  for(int i=0; i<N; i++) {
    if(!destroy[i]) {
      newindex++;
      new2old[newindex] = i;
      old2new.insert(pair<int,int>(i,newindex));
    }
  }

  int c = 0;
  for (auto const& pp : old2new) {
    printf("%d => %d, %d => %d\n", pp.first, pp.second, c, new2old[c]);
    c++;
  }
  printf("~~~\n");

  destroy_nodes(grafo);
  destroy.clear();

  int newi = -1;
  int newv = -1;

  for(int i=0; i<N; i++) {
    if(grafo[i].active) {
      newi = old2new[i];
      tmpgrafo[newi].dist = grafo[i].dist;
      tmpgrafo[newi].active = true;
      for (int v: grafo[i].adj) {
          newv = old2new[v];
          tmpgrafo[newi].adj.push_back(newv);
      }
    }
  }

  grafo.clear();
  grafo.swap(tmpgrafo);

  print_g(grafo);
  printf("***\n");

  for(int i=0; i<grafo.size(); i++) {
    destroy[i] = false;
  }

  grafoT.resize(grafo.size());

  for(int i=0; i<grafo.size(); i++) {
    for (int v: grafo[i].adj) {
      grafoT[v].adj.push_back(i);
    }
  }

  print_g(grafoT);
  printf("***\n");

  int newS = old2new[S];
  printf("S: %d, newS: %d\n", S, newS);
  bfs(S, grafoT);

  for(int i=0; i<grafo.size(); i++) {
    if((grafo[i].dist == -1) or (grafoT[i].dist == -1) or (grafo[i].dist + grafoT[i].dist > K)) {
      printf("destroied node: %d\n", i);
      destroy[i] = true;
      count_destroied++;
    }
  }
  remaining = N-count_destroied;

  printf("-> nodes: %d\n", N);
  printf("-> destroyed: %d\n", count_destroied);
  printf("-> remaining: %d\n", remaining);

  destroy_nodes(grafo);

  map<int,int> tmp_old2new;
  vector<int> tmp_new2old;
  tmp_new2old.resize(remaining);

  newindex = -1;
  int oldi = -1;
  for(int i=0; i<grafo.size(); i++) {
    if(!destroy[i]) {
      newindex++;

      oldi = new2old[i];

      printf("newindex: %d\n", newindex);
      printf("i: %d - oldi: %d\n", i, oldi);

      tmp_new2old[newindex] = oldi;
      tmp_old2new.insert(pair<int,int>(oldi, newindex));
      printf("tmp_new2old[%d]: %d\n", newindex, tmp_new2old[newindex]);
      printf("tmp_old2new.insert(pair<int,int>(%d, %d))\n", oldi, newindex);

    }
  }

  printf("*** tmp maps ***\n");
  printf("tmp_old2new, tmp_new2old\n");
  c = 0;
  for (auto const& pp : tmp_old2new) {
    printf("%d => %d, %d => %d\n", pp.first, pp.second, c, tmp_new2old[c]);
    c++;
  }
  printf("^^^\n");

  printf("*** maps ***\n");
  printf("old2new, new2old\n");
  c = 0;
  for (auto const& pp : old2new) {
    printf("%d => %d, %d => %d\n", pp.first, pp.second, c, new2old[c]);
    c++;
  }
  printf("~~~\n");

  printf("*** 1 ***\n");

  newi = -1;
  newv = -1;
  int tmpnewi = -1;
  int tmpnewv = -1;
  int oldv = -1;

  tmpgrafo.resize(remaining);
  for(int i=0; i<grafo.size(); i++) {
    if(grafo[i].active) {

    	oldi = new2old[i];
    	tmpnewi = tmp_old2new[oldi];
      printf("i: %d, oldi: %d, tmpnewi: %d\n", i, oldi, tmpnewi);

      tmpgrafo[tmpnewi].dist = grafo[i].dist;
      tmpgrafo[tmpnewi].active = true;
      for (int v: grafo[i].adj) {

	    	oldv = new2old[v];
  	  	tmpnewv = tmp_old2new[oldv];
	      printf("v: %d, oldv: %d, tmpnewv: %d\n", v, oldv, tmpnewv);

        tmpgrafo[tmpnewi].adj.push_back(tmpnewv);
      }
    }
  }

  grafo.clear();
  grafo.swap(tmpgrafo);

  printf("*** 2 ***\n");
  new2old.clear();
  old2new.clear();

  printf("*** 3 ***\n");
  tmp_new2old.swap(new2old);
  tmp_old2new.swap(old2new);

  printf("*** 4 ***\n");

  c = 0;
  for (auto const& pp : old2new) {
    printf("%d => %d, %d => %d\n", pp.first, pp.second, c, new2old[c]);
    c++;
  }
  printf("~~~\n");

  print_g(grafo);
  printf("---\n");

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
	printf("grafo.size(): %zu\n", grafo.size());
	oldi = -1;
  for (int i=0; i<grafo.size(); i++) {
    if(grafo[i].score != 0.0) {
    	oldi = new2old[i];
      printf("score(%d): %f\n", oldi, grafo[i].score);
    }
  }

  return 0;
}
