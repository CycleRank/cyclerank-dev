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
#include <stdlib.h>     /* exit, EXIT_FAILURE */

#include "cxxopts.hpp"
#include "spdlog/spdlog.h"

using namespace std;
namespace spd = spdlog;
namespace opts = cxxopts;

// ***************************************************************************
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

// *************************************************************************
// global variables
shared_ptr<spd::logger> console;

vector<stack<int>> cycles;
stack<int> tarjan_st;
int counter = 0;

stack<int> circuits_st;

// *************************************************************************
// helper functions
void print_g(vector<nodo>& g) {
  for (int i=0; i<g.size(); i++) {
    if (g[i].active) {
      for (int v: g[i].adj) {
        console->debug("{0:d} -> {1:d}", i, v);
      }
    }
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
// ********** end: helper functions


// *************************************************************************
void destroy_nodes(vector<nodo>& g, vector<bool>& destroy) {

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


void bfs(int source, int K, vector<nodo>& g) {

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


void unblock(int u, vector<nodo>& g) {
  // printf("      ----> unblock(%d)\n", u);
  g[u].blocked = false;
  // printf("        ----> g[%d].blocked: %s\n", u, g[u].blocked ? "true" : "false");

  while (!g[u].B.empty()) {
    int w = g[u].B.front();
    g[u].B.pop_front();

    if (g[w].blocked) {
      unblock(w, g);
    }
  }
}


bool circuit(int v, int S, int K, vector<nodo>& g) {
  bool flag = false;

  circuits_st.push(v);

  g[v].blocked = true;

  for(int w : g[v].adj) {
    if (w == S) {
      if (!(circuits_st.size() > K)) {
        cycles.push_back(circuits_st);
      }
      flag = true;
    } else if (!g[w].blocked) {
      if (circuit(w, S, K, g)) {
        flag = true;
      }
    }
  }

  if (flag) {
    unblock(v, g);
  } else {
    for (int w: g[v].adj) {
      auto it = find(g[w].B.begin(), g[w].B.end(), v);
      if (it == g[w].B.end()) {
        g[w].B.push_back(v);
      }
    }
  }

  circuits_st.pop();

  return flag;
}


int main(int argc, const char* argv[]) {

	// *************************************************************************
	// initialize logger
  try {
		console = spd::stdout_color_mt("console");
  }
  // exceptions thrown upon failed logger init
  catch (const spd::spdlog_ex& ex) {
      cerr << "Log init failed: " << ex.what() << endl;
      return 1;
  }
	// ********** end: logger
	
	// *************************************************************************
	// parse command-line options
  opts::Options* options;
  string input_file="input.txt";
  bool verbose = false;
	bool debug = false;

  try {

    options = new cxxopts::Options(argv[0]);

    options->add_options()
      ("f,file", "File", cxxopts::value<std::string>(input_file))
      ("v,verbose", "Verbose", cxxopts::value(verbose))
      ("d,debug", "Debug", cxxopts::value(debug))
      ;

		auto arguments = options->parse(argc, argv);
  } catch (const cxxopts::OptionException& e) {
    cerr << "error parsing options: " << e.what() << endl;
    exit (EXIT_FAILURE);
  }
	// ********** end: command-line options

	// *************************************************************************
	// set logging level based on option from CLI
  if (debug) {
  	spd::set_level(spd::level::debug);
  } else if (verbose) {
  	spd::set_level(spd::level::info);
  } else {
  	spd::set_level(spd::level::warn);
  }

  console->info("Log start!");
  console->debug("input_file: {}", input_file);
  console->debug("verbose: {}", verbose);
  console->debug("debug: {}", debug);

	// *************************************************************************
	// start algorithm
	int N, M, S, K;

	vector<nodo> grafo;
	vector<nodo> grafoT;

	vector<bool> destroy;

  map<int,int> old2new;
  vector<int> new2old;

	// *************************************************************************
	// read input
	ifstream in(input_file);

  in >> N >> M >> S >> K;

  grafo.resize(N);
  destroy.resize(N);

  for(int i=0; i<N; i++) {
    destroy[i] = false;
  }

  console->info("Reading graph");
  for(int i=0; i<M; i++) {
    int s, t;
    in >> s >> t;
    grafo[s].adj.push_back(t);
  }
  console->info("Read graph");

  // print_g(grafo);
  // console->debug("---\n");

  console->info("Step 1. BFS");
  bfs(S, K, grafo);

  int count_destroied = 0;
  for(int i=0; i<N; i++) {

    // se il nodo si trova distanza maggiore di K-1 o non raggiungibile
    if((grafo[i].dist == -1) or (grafo[i].dist > K-1)) {
      // console->debug("destroied node: {0:d}", i);
      destroy[i] = true;
      count_destroied++;
    }
  }

  int remaining = N-count_destroied;

  console->info("nodes: {}", N);
  console->info("destroyed: {}", count_destroied);
  console->info("remaining: {}", remaining);

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
    console->debug("{0:d} => {1:d}, {2:d} => {3:d}",
    							 pp.first,
    							 pp.second,
    							 c,
    							 new2old[c]);
    c++;
  }
  console->debug("~~~");

  destroy_nodes(grafo, destroy);
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

  // print_g(grafo);
  // console->debug("***\n");

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
  console->debug("***");

  int newS = old2new[S];

  console->info("S: {0}, newS: {1}", S, newS);
  console->info("Step 2. BFS");
  bfs(newS, K, grafoT);

  for(int i=0; i<grafo.size(); i++) {
    if((grafo[i].dist == -1) or (grafoT[i].dist == -1) or (grafo[i].dist + grafoT[i].dist > K)) {
      // console->debug("destroied node: {0:d}\n", i);
      destroy[i] = true;
      count_destroied++;
    }
  }
  remaining = N-count_destroied;

  console->info("nodes: {}", N);
  console->info("destroyed: {}", count_destroied);
  console->info("remaining: {}", remaining);

  destroy_nodes(grafo, destroy);

  map<int,int> tmp_old2new;
  vector<int> tmp_new2old;
  tmp_new2old.resize(remaining);

  newindex = -1;
  int oldi = -1;
  for(int i=0; i<grafo.size(); i++) {
    if(!destroy[i]) {
      newindex++;

      oldi = new2old[i];

      console->debug("newindex: {}", newindex);
      console->debug("i: {} - oldi: {}", i, oldi);

      tmp_new2old[newindex] = oldi;
      tmp_old2new.insert(pair<int,int>(oldi, newindex));
      console->debug("tmp_new2old[{0}]: {1}",
      							 newindex,
      							 tmp_new2old[newindex]);
      console->debug("tmp_old2new.insert(pair<int,int>({0}, {1}))",
      							 oldi,
      							 newindex);
    }
  }

  console->debug("*** tmp maps ***");
  console->debug("tmp_old2new, tmp_new2old");
  c = 0;
  for (auto const& pp : tmp_old2new) {
    console->debug("{0} => {1}, {2} => {3}",
    							 pp.first,
    							 pp.second,
    							 c,
    							 tmp_new2old[c]);
    c++;
  }
  console->debug("^^^");

  console->debug("*** maps ***");
  console->debug("old2new, new2old");
  c = 0;
  for (auto const& pp : old2new) {
    console->debug("{0} => {1}, {2} => {3}",
							   	 pp.first,
							   	 pp.second,
							   	 c,
							   	 new2old[c]);
    c++;
  }
  console->debug("~~~");

  console->debug("*** 1 ***");

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
      console->debug("i: %d, oldi: %d, tmpnewi: %d\n", i, oldi, tmpnewi);

      tmpgrafo[tmpnewi].dist = grafo[i].dist;
      tmpgrafo[tmpnewi].active = true;
      for (int v: grafo[i].adj) {

	    	oldv = new2old[v];
  	  	tmpnewv = tmp_old2new[oldv];
	      console->debug("v: %d, oldv: %d, tmpnewv: %d\n", v, oldv, tmpnewv);

        tmpgrafo[tmpnewi].adj.push_back(tmpnewv);
      }
    }
  }

  grafo.clear();
  grafo.swap(tmpgrafo);

  console->debug("*** 2 ***\n");
  new2old.clear();
  old2new.clear();

  console->debug("*** 3 ***\n");
  tmp_new2old.swap(new2old);
  tmp_old2new.swap(old2new);

  console->debug("*** 4 ***\n");

  c = 0;
  for (auto const& pp : old2new) {
    console->debug("{0:d} => {1:d}, {2:d} => {3:d}",
    							 pp.first,
    							 pp.second,
    							 c,
    							 new2old[c]);
    c++;
  }
  console->debug("~~~\n");

  print_g(grafo);
  console->debug("---\n");

  newS = old2new[S];
  console->info("S: {0}, newS: {1}", S, newS);
  circuit(newS, newS, K, grafo);

  print_cycles();
  console->debug("***\n");

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

  console->debug("---\n");
	console->debug("grafo.size(): %zu\n", grafo.size());
	oldi = -1;
  for (int i=0; i<grafo.size(); i++) {
    if(grafo[i].score != 0.0) {
    	oldi = new2old[i];
      printf("score(%d): %f\n", oldi, grafo[i].score);
    }
  }

  console->info("Log stop!", input_file);
  exit (EXIT_SUCCESS);
}
