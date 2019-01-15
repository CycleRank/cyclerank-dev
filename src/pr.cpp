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

extern "C" {
   #include <igraph.h>
}

#include "cxxopts.hpp"
#include "spdlog/spdlog.h"

using namespace std;
namespace spd = spdlog;
namespace opts = cxxopts;

// ***************************************************************************
struct nodo{
  bool active;
  bool blocked;
  int dist;
  vector<int> adj;
  list<int> B;

  nodo(){
    active = true;
    blocked = false;
    dist = -1;
    B.clear();
  }
};


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
  int firstline_count =0;
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
void transpose_graph(vector<nodo>& g, vector<nodo>& gT) {
  gT.resize(g.size());

  for(unsigned int i=0; i<g.size(); i++) {
    for (int v: g[i].adj) {
      gT[v].adj.push_back(i);
    }
  }
}


void destroy_nodes(vector<nodo>& g, vector<bool>& destroy) {

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


void bfs(int source, unsigned int K, vector<nodo>& g) {

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
  bool verbose = false;
  bool debug = false;
  bool help = false;
  bool transposed = false;
  bool undirected = false;
  bool directed = true;
  bool wholenetwork = false;
  bool forcebfstransposed = false;

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
      ("o,output", "Output file.",
       cxxopts::value<string>(output_file),
       "OUTPUT_FILE"
       )
      ("t,transposed", "Run on the transposed network (incompatible with -u).",
       cxxopts::value(transposed))
      ("u,undirected", "Run on the undirected network (incompatible with -t).",
       cxxopts::value(undirected))
      ("b,force-bfs-transposed", "Force running the second BFS on the " \
       "transposed network. This is needed only if -u is specified, " \
       "otherwise it is effectively ignored.",
       cxxopts::value(forcebfstransposed))
      ("w,whole-network", "Run on the whole network (ignore K).",
       cxxopts::value(wholenetwork))
      ;

    auto arguments = options->parse(argc, argv);
  } catch (const cxxopts::OptionException& e) {
    cerr << "Error parsing options: " << e.what() << endl;
    exit (EXIT_FAILURE);
  }

  // if help option is activated, print help and exit.
  if(help) {
    cout << options->help({""}) << endl;
    exit(0);
  }

  if(transposed && undirected) {
    cerr << "Error: options -t (transposed) and -u (undirected) are " \
         << "mutually exclusive." << endl;
    exit (EXIT_FAILURE);
  }

  // use a variable called directed to indicate if the graph is directed
  directed = !undirected;
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
  console->debug("transposed: {}", transposed);
  console->debug("undirected: {}", undirected);
  console->debug("directed: {}", directed);
  console->debug("whole-network: {}", wholenetwork);
  // ********** end: start logging

  // *************************************************************************
  // start algorithm
  unsigned int N = 0, M = 0;
  vector<nodo> grafo;

  map<int,int> old2new;
  vector<int> new2old;

  // *************************************************************************
  // read input
  {
    ifstream in(input_file);
    int nparam = 0;

    if(in.fail()){
      cerr << "Error! Could not open file: " << input_file << endl;
      exit(EXIT_FAILURE);
    }

    nparam = count_parameters(in);
    in.close();

    in.open(input_file);
    if(nparam == 2) {
      in >> N >> M;
    } else {
      cerr << "Error! Error while reading file (" << input_file \
           << "), unexpected number of parameters" << endl;
      exit(EXIT_FAILURE);
    }

    assert( (N > 0 && M > 0) \
            && "N and M must be positive." );

    console->info("N: {}", N);
    console->info("M: {}", M);

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

        if(!directed) {
          // we still need to check for duplicates since we are starting
          // from a directed network and if we a double link, i.e.:
          //   1 -> 2
          //   2 -> 1
          // this would become a duplicate when considering the undirected
          // version
          if (find(grafo[t].adj.begin(), \
                   grafo[t].adj.end(), \
                   s) == grafo[t].adj.end()) {
            grafo[t].adj.push_back(s);
          }
        }
      }
    }
    console->debug("--> read graph");
    in.close();
  }
  // ********** end: read input

  /* *************************************************************************
  * Pagerank from igraph
  *   https://igraph.org/c/doc/igraph-Structural.html#igraph_pagerank
  *
  * int igraph_pagerank(
  *   const igraph_t *graph,
  *   igraph_pagerank_algo_t algo,
  *   igraph_vector_t *vector,
  *   igraph_real_t *value, const igraph_vs_t vids,
  *   igraph_bool_t directed, igraph_real_t damping, 
  *   const igraph_vector_t *weights, void *options
  *   );
  * *************************************************************************/
  console->info("Pagerank");

  igraph_t igrafo;
  igraph_vector_t iedges;
  vector<nodo> grafoT;
  vector<nodo> grafoU;

  console->debug("Calculating the Pagerank on the graph: ");
  if(!transposed) {
    console->debug("  * on the input graph");
  } else {
    console->debug("  * on the transposed graph");
    transpose_graph(grafo, grafoT);
    grafo.swap(grafoT);

    // deallocate vector (of nodes)
    grafoT.clear();
  }

  if(directed) {
    console->debug("  * on the directed graph");
  } else {
    console->debug("  * on the undirected graph");
  }

  // count number of edges
  unsigned int num_edges = 0;
  for(unsigned int i=0; i<grafo.size(); i++) {
    num_edges += grafo[i].adj.size();
  }

  console->debug("num_edges: {0}", num_edges);

  // initialize vertices vector 2*num_edges
  igraph_vector_init(&iedges, 2*num_edges);

  int ec = 0;
  for(unsigned int i=0; i<grafo.size(); i++) {
    for (int v: grafo[i].adj) {
      VECTOR(iedges)[ec]=i;
      VECTOR(iedges)[ec+1]=v;

      ec = ec + 2;
    }
  }

  // we get the size of the graph and the we clear
  unsigned int num_nodes = grafo.size();
  grafo.clear();

  // int igraph_create(igraph_t *graph, const igraph_vector_t *edges,
  //   igraph_integer_t n, igraph_bool_t directed);
  igraph_create(&igrafo, &iedges, num_nodes, directed);

  igraph_vector_t pprscore;

  // init result vector
  igraph_vector_init(&pprscore, 0);

  /*
  * int igraph_pagerank(
  *   const igraph_t *graph,
  *   igraph_pagerank_algo_t algo,
  *   igraph_vector_t *vector,
  *   igraph_real_t *value,
  *   const igraph_vs_t vids,
  *   igraph_bool_t directed, 
  *   igraph_real_t damping, 
  *   const igraph_vector_t *weights,
  *   void *options);
  *
  *
  * graph:    The graph object.
  * algo:     The PageRank implementation to use {IGRAPH_PAGERANK_ALGO_POWER,
              IGRAPH_PAGERANK_ALGO_ARPACK, IGRAPH_PAGERANK_ALGO_PRPACK}.
  *           IGRAPH_PAGERANK_ALGO_PRPACK is the recommended implementation
  *           http://igraph.org/c/doc/igraph-Structural.html#igraph_pagerank_algo_t
  * vector:   Pointer to an initialized vector, the result is stored here.
  *           It is resized as needed.
  * value:    Pointer to a real variable, the eigenvalue corresponding to the
              PageRank vector is stored here. It should be always exactly one.
  * vids:     The vertex ids for which the PageRank is returned.
  * directed: Boolean, whether to consider the directedness of the edges.
              This is ignored for undirected graphs.
  * damping:  The damping factor ("d" in the original paper)
  * weights:  Optional edge weights, it is either a null pointer, then the
              edges are not weighted, or a vector of the same length as the
              number of edges.
  * options:  Options to the algorithms.
  *
  */

  int ret = -1;
  ret=igraph_pagerank(
     &igrafo,                         // const igraph_t *graph
     IGRAPH_PAGERANK_ALGO_PRPACK,     // igraph_pagerank_algo_t algo
     &pprscore,                       // igraph_vector_t *vector
     0,                               // igraph_real_t *value
     igraph_vss_all(),                // const igraph_vs_t vids
     directed,                        // igraph_bool_t directed
     0.85,                            // igraph_real_t damping
     0,                               // const igraph_vector_t *weights,
     0                                // void *options
     );
  console->debug("PR ret: {0:d}", ret);

  igraph_destroy(&igrafo);

  FILE* outfp;
  outfp = fopen(output_file.c_str(), "w+");
  for (unsigned int i=0; i<num_nodes; i++) {
    int oldi;
    if(!wholenetwork) {
      oldi = new2old[i];
    } else {
      oldi = i;
    }
    fprintf(outfp, "score(%d):\t%.10f\n", oldi, VECTOR(pprscore)[i]);
  }

  console->info("Log stop!");
  exit (EXIT_SUCCESS);
}
