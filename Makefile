help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

build: pageloop_back_map ## Generates pageloop_back_map binary

pageloop_back_map: src/pageloop_back_map.cpp
	${CXX} -Wall -Werror -std=c++11 -O2 -flto -pipe \
			-pthread \
			-Ilibs \
			-o pageloop_back_map \
			src/pageloop_back_map.cpp

clean:  ## Remove generated binary and object files
	rm -f pageloop_back_map
