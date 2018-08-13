#include <list>
#include <vector>
#include <fstream>
#include <initializer_list>

#include "node.h"
#include "interruptible.h"

using namespace std;


// Fastest way to check if a file exist using standard C++/C++11/C?
// https://stackoverflow.com/a/12774387/2377454
bool interruptible::file_exists (const string& filename) {
  struct stat buffer;   
  return (stat (filename.c_str(), &buffer) == 0); 
}


initializer_list<pair<string const, int>> il = {
  {"pageloop.afterstage1", 1},
  {"pageloop.afterstage2", 2}
};

map<string, int> restart_values{il};

int interruptible::read_restart (const string& filename) {
  ifstream in(filename);
  string line;
  int result = -1;

  // read first line of file
  getline(in, line);

  result = restart_values[line];

  return result;
}

void interruptible::dump (const vector<node>& grafo) {
  return;
}

void interruptible::dump (const map<int,int>& old2new) {
  return;
}

void interruptible::dump (const vector<int>& new2old) {
  return;
}
