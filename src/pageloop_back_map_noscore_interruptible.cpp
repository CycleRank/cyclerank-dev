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
#include "pageloop/node.h"
#include "pageloop/interruptible.h"

using namespace std;
namespace spd = spdlog;
namespace opts = cxxopts;

// *************************************************************************
// global variables
shared_ptr<spd::logger> console;

// *************************************************************************
// helper functions
void print_circuit(stack<int> s, vector<int>& new2old) {
  vector<int> tmp;

  printf("--> cycle: ");
  while (!s.empty()) {
    int el = s.top();
    int oldel = new2old[el];
    tmp.push_back(oldel);
    s.pop();
  }

  for (int k=tmp.size()-1; k>=0; k--) {
    printf("%d-", tmp[k]);
  }
  int last = tmp[tmp.size()-1];
  printf("%d\n", last);

}

void write_circuit(stack<int> s, vector<int>& new2old, ofstream& out) {
  vector<int> tmp;

  while (!s.empty()) {
    int el = s.top();
    int oldel = new2old[el];
    tmp.push_back(oldel);
    s.pop();
  }

  for (unsigned k=tmp.size()-1; k>0; k--) {
    out << tmp[k] << " ";
  }
  out << tmp[0] << endl;
}

// count the number of parameters in the first line of the file
// https://stackoverflow.com/a/34665370/2377454
int count_parameters(ifstream& in) {

  int tmp_n;
  int firstline_count = 0;
  string line;

  // read first line of file
  getline(in, line);

  stringstream ss(line);

  // read numbers from the line
  while (ss >> tmp_n) {
    ++firstline_count;
  }

  console->debug("firstline_count: {}", firstline_count);

  return firstline_count;
}

// get remapped node
int get_remapped_node_or_fail(int s, map<int,int>& map_old2new ) {
  int newS = -1;

  if ( map_old2new.find(s) == map_old2new.end() ) {
    // Key s not found
    cerr << "Key " << s << " not found in map" << endl;
    exit(EXIT_FAILURE);
  } else {
    // Key s found
    newS = map_old2new[s];
    return newS;
  }

}
// ********** end: helper functions


// *************************************************************************
void destroy_nodes(vector<node>& g, vector<bool>& destroy) {

  for(unsigned int i=0; i<g.size(); i++) {
    if (destroy[i]) {
      g[i].active = false;
      g[i].adj.clear();
    } else {
      for (unsigned int j=0; j<g[i].adj.size(); j++) {
        int v = g[i].adj[j];
        if (destroy[v]) {
          g[i].adj.erase(g[i].adj.begin()+j);
        }
      }
    }
  }
}


void bfs(int source, unsigned int K, vector<node>& g) {

  if (!g[source].active) {
    return;
  }

  for (node& n: g) {
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
    if(g[cur].dist > (int) K-2) {
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


void unblock(int u, vector<node>& g) {
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


int count_calls=0;
bool circuit(int v, int S, unsigned int K,
             vector<node>& g,
             vector<int>& new2old,
             stack<int>& circuits_st,
             ofstream& out) {
  bool flag = false;

  /*
  if interruptible::file_exists("pageloop.stopme") {

  }
  */

  if (!(circuits_st.size() > K-1)) {
    count_calls++;

    circuits_st.push(v);

    g[v].blocked = true;

    for(int w : g[v].adj) {
      if (w == S) {
        if (!(circuits_st.size() > K)) {
          write_circuit(circuits_st, new2old, out);
        }
        flag = true;
      } else if (!g[w].blocked) {
        if (circuit(w, S, K, g, new2old, circuits_st, out)) {
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
  }

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
  string output_file="output.txt";
  int cliS = -1;
  int cliK = -1;
  bool verbose = false;
  bool debug = false;
  bool help = false;

  try {
    options = new cxxopts::Options(argv[0]);

    options->add_options()
      ("f,file", "Input file.",
       cxxopts::value<string>(input_file),
       "FILE"
       )
      ("v,verbose", "Enable logging at verbose level.",
       cxxopts::value(verbose))
      ("d,debug", "Enable logging at debug level.",
       cxxopts::value(debug))
      ("h,help", "Show help message and exit.",
       cxxopts::value(help))
      ("k,maxloop", "Set max loop length (K).",
       cxxopts::value(cliK),
       "K"
       )
      ("o,output", "Output file.",
       cxxopts::value<string>(output_file),
       "OUTPUT_FILE"
       )
      ("s,source", "Set source node (S).",
       cxxopts::value(cliS),
       "S"
       )
      ;

    auto arguments = options->parse(argc, argv);
  } catch (const cxxopts::OptionException& e) {
    cerr << "error parsing options: " << e.what() << endl;
    exit (EXIT_FAILURE);
  }

  // if help option is activated, print help and exit.
  if(help) {
    cout << options->help({""}) << endl;
    exit(0);
  }
  // ********** end: parse command-line options

  // *************************************************************************
  // start logging
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
  // ********** end: start logging

  // *************************************************************************
  // start algorithm
  int S = -1, newS = -1;
  unsigned int N = 0, M = 0, K = 0;
  vector<node> grafo;

  map<int,int> old2new;
  vector<int> new2old;

  int count_destroied = 0;

  if (interruptible::file_exists("pageloop.stopme")) {
    interruptible::read_restart("pageloop.restart");
  }

  // *************************************************************************
  // read input
  {
    ifstream in(input_file);
    int tmpS = -1;
    int tmpK = -1;
    int nparam = 0;

    if(in.fail()){
      cerr << "Error! Could not open file: " << input_file << endl;
      exit(EXIT_FAILURE);
    }

    nparam = count_parameters(in);
    in.close();

    in.open(input_file);
    if(nparam == 4) {
      in >> N >> M >> tmpS >> tmpK;
    } else if(nparam == 2) {
      in >> N >> M;
    } else {
      cerr << "Error! Error while reading file (" << input_file \
          << "), unexpected number of parameters" << endl;
      exit(EXIT_FAILURE);
    }

    if(cliS == -1) {
      S = tmpS;
    } else {
      S = cliS;
    }

    if(cliK == -1) {
      K = (unsigned int) tmpK;
    } else {
      K = (unsigned int) cliK;
    }

    assert( (N > 0 && M > 0) \
            && "N and M must be positive." );

    assert( (K > 0 && S >= 0) \
            && "K must be positive and S must be non-negative." );

    console->info("N: {}", N);
    console->info("M: {}", M);
    console->info("S: {}", S);
    console->info("K: {}", K);

    console->debug("reading graph...");
    grafo.resize(N);
    for(unsigned int j=0; j<M; j++) {
      int s, t;
      in >> s >> t;
      // check that we are not inserting duplicates
      if (find(grafo[s].adj.begin(), \
               grafo[s].adj.end(), \
               t) == grafo[s].adj.end()) {
        grafo[s].adj.push_back(t);
      }
    }
    console->debug("--> read graph");
    in.close();
  }
  // ********** end: read input


  // *************************************************************************
  // Step 1: BFS on g
  {
    console->info("Step 1. BFS");
    vector<bool> destroy(N, false);

    bfs(S, K, grafo);

    for(unsigned int i=0; i<N; i++) {
      // se il nodo si trova distanza maggiore di K-1 o non raggiungibile
      if((grafo[i].dist == -1) or (grafo[i].dist > (int) K-1)) {
        destroy[i] = true;
        count_destroied++;
      }
    }

    int remaining = N-count_destroied;
    console->info("nodes: {}", N);
    console->info("destroyed: {}", count_destroied);
    console->info("remaining: {}", remaining);
    new2old.resize(remaining);

    int newindex = -1;
    for(unsigned int i=0; i<N; i++) {
      if(!destroy[i]) {
        newindex++;
        new2old[newindex] = i;
        old2new.insert(pair<int,int>(i,newindex));
        /*
        console->debug("old2new.insert(pair<int,int>({0}, {1}))",
                       i,
                       newindex);
        */
      }
    }

    if(debug) {
      console->debug("index map (1)");
      console->debug("old2new.size() is {}", old2new.size());

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
    }

    destroy_nodes(grafo, destroy);

    vector<node> tmpgrafo;
    tmpgrafo.resize(remaining);

    int newi = -1;
    int newv = -1;

    for(unsigned int i=0; i<N; i++) {
      if(grafo[i].active) {
        newi = old2new[i];
        tmpgrafo[newi].dist = grafo[i].dist;
        tmpgrafo[newi].active = true;
        for (int v: grafo[i].adj) {
          if(grafo[v].active) {
            newv = old2new[v];
            tmpgrafo[newi].adj.push_back(newv);
          }
        }
      }
    }

    grafo.clear();
    grafo.swap(tmpgrafo);

    destroy.clear();
  }
  // ********** end: Step 1

  if (interruptible::file_exists("pageloop.stopme")) {
    interruptible::dump(grafo);
    interruptible::dump(old2new);
    interruptible::dump(new2old);
  }

  vector<bool> destroy(grafo.size(), false);


  // *************************************************************************
  // get remapped source node (S)
  newS = get_remapped_node_or_fail(S, old2new);
  console->info("S: {0}, newS: {1}", S, newS);
  // ********** end: get remapped source node (S)

  // *************************************************************************
  // Step 2: BFS on g^T
  {
    console->info("Step 2.: BFS on g^T");
    vector<node> grafoT;
    grafoT.resize(grafo.size());

    for(unsigned int i=0; i<grafo.size(); i++) {
      for (int v: grafo[i].adj) {
        grafoT[v].adj.push_back(i);
      }
    }

    bfs(newS, K, grafoT);

    for(unsigned int i=0; i<grafo.size(); i++) {
      if((grafo[i].dist == -1) or (grafoT[i].dist == -1) or \
          (grafo[i].dist + grafoT[i].dist > (int) K)) {
        // console->debug("destroied node: {0:d}\n", i);
        destroy[i] = true;
        count_destroied++;
      }
    }

    int remaining = N-count_destroied;

    console->info("nodes: {}", N);
    console->info("destroyed: {}", count_destroied);
    console->info("remaining: {}", remaining);

    destroy_nodes(grafo, destroy);
  }
  // ********** end: Step 2

  int remaining = N-count_destroied;
  map<int,int> tmp_old2new;
  vector<int> tmp_new2old;
  tmp_new2old.resize(remaining);

  {
    int newindex = -1;
    int oldi = -1;
    for(unsigned int i=0; i<grafo.size(); i++) {
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
  }

  if(debug) {
    console->debug("*** tmp maps ***");
    console->debug("tmp_old2new, tmp_new2old");
    console->debug("tmp_old2new.size() is {}", tmp_old2new.size());

    int c = 0;
    for (auto const& pp : tmp_old2new) {
      console->debug("{0:d} => {1:d}, {2:d} => {3:d}",
                     pp.first,
                     pp.second,
                     c,
                     tmp_new2old[c]);
      c++;
    }

    console->debug("*** maps BBB ***");
    console->debug("old2new.size() is {}", old2new.size());
    console->debug("old2new, new2old");
    c = 0;
    for (auto const& pp : old2new) {
      console->debug("{0:d} => {1:d}, {2:d} => {3:d}",
                     pp.first,
                     pp.second,
                     pp.second,
                     new2old[pp.second]);
      c++;
    }
    console->debug("~~~");

    console->debug("*** 1 ***");
  }

  {
    int oldi = -1, tmpnewi = -1;
    int oldv = -1, tmpnewv = -1;

    vector<node> tmpgrafo;
    tmpgrafo.resize(remaining);
    for(unsigned int i=0; i<grafo.size(); i++) {
      if(grafo[i].active) {

        oldi = new2old[i];
        tmpnewi = tmp_old2new[oldi];
        tmpgrafo[tmpnewi].dist = grafo[i].dist;
        tmpgrafo[tmpnewi].active = true;
        for (int v: grafo[i].adj) {
          if(grafo[v].active) {
            oldv = new2old[v];
            tmpnewv = tmp_old2new[oldv];
            tmpgrafo[tmpnewi].adj.push_back(tmpnewv);
          }
        }
      }
    }

    grafo.clear();
    grafo.swap(tmpgrafo);
    destroy.clear();
  }

  new2old.clear();
  old2new.clear();

  tmp_new2old.swap(new2old);
  tmp_old2new.swap(old2new);


  if(debug) {
    console->debug("map indexes");
    console->debug("old2new.size() is {}", old2new.size());

    for (auto const& pp : old2new) {
      console->debug("{0:d} => {1:d}, {2:d} => {3:d}",
                     pp.first,
                     pp.second,
                     pp.second,
                     new2old[pp.second]);
    }
    console->debug("~~~");
  }

  if (interruptible::file_exists("pageloop.stopme")) {
    interruptible::dump(grafo);
    interruptible::dump(old2new);
    interruptible::dump(new2old);
  }

  // *************************************************************************
  // get remapped source node (S)
  newS = get_remapped_node_or_fail(S, old2new);
  console->info("S: {0}, newS: {1}", S, newS);
  // ********** end: get remapped source node (S)

  console->debug("calling circuit()");

  ofstream out(output_file);
  stack<int> circuits_st;
  circuit(newS, newS, K, grafo, new2old, circuits_st, out);
  out.close();

  console->debug("count_calls: {}", count_calls);
  console->debug("called circuit()");

  console->info("Log stop!");
  exit (EXIT_SUCCESS);
}
