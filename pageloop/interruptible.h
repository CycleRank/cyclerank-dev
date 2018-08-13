#ifndef INTERRUPTIBLE_H
#define INTERRUPTIBLE_H

#include <map>
#include <string>
#include <vector>
#include <sys/stat.h>

#include "node.h"

using namespace std;

namespace interruptible {
  bool file_exists(const string& filename);
  int read_restart(const string& filename);

  void dump(const vector<node>& grafo);
  void dump(const map<int,int>& old2new);
  void dump(const vector<int>& new2old);
}

#endif
#pragma once
