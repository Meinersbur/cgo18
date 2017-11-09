# Install script for directory: /users/krusemi/scratch/execslave/persistent/persistent4/llvm/projects/test-suite/Performance/Polybench-421/linear-algebra/solvers

# Set the install prefix
if(NOT DEFINED CMAKE_INSTALL_PREFIX)
  set(CMAKE_INSTALL_PREFIX "/usr/local")
endif()
string(REGEX REPLACE "/$" "" CMAKE_INSTALL_PREFIX "${CMAKE_INSTALL_PREFIX}")

# Set the install configuration name.
if(NOT DEFINED CMAKE_INSTALL_CONFIG_NAME)
  if(BUILD_TYPE)
    string(REGEX REPLACE "^[^A-Za-z0-9_]+" ""
           CMAKE_INSTALL_CONFIG_NAME "${BUILD_TYPE}")
  else()
    set(CMAKE_INSTALL_CONFIG_NAME "Release")
  endif()
  message(STATUS "Install configuration: \"${CMAKE_INSTALL_CONFIG_NAME}\"")
endif()

# Set the component getting installed.
if(NOT CMAKE_INSTALL_COMPONENT)
  if(COMPONENT)
    message(STATUS "Install component: \"${COMPONENT}\"")
    set(CMAKE_INSTALL_COMPONENT "${COMPONENT}")
  else()
    set(CMAKE_INSTALL_COMPONENT)
  endif()
endif()

# Install shared libraries without execute permission?
if(NOT DEFINED CMAKE_INSTALL_SO_NO_EXE)
  set(CMAKE_INSTALL_SO_NO_EXE "0")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for each subdirectory.
  include("/scratch/shared/leone/krusemi/execslave/work/work4/run-test-suite/Performance/Polybench-421/linear-algebra/solvers/cholesky/cmake_install.cmake")
  include("/scratch/shared/leone/krusemi/execslave/work/work4/run-test-suite/Performance/Polybench-421/linear-algebra/solvers/durbin/cmake_install.cmake")
  include("/scratch/shared/leone/krusemi/execslave/work/work4/run-test-suite/Performance/Polybench-421/linear-algebra/solvers/gramschmidt/cmake_install.cmake")
  include("/scratch/shared/leone/krusemi/execslave/work/work4/run-test-suite/Performance/Polybench-421/linear-algebra/solvers/lu/cmake_install.cmake")
  include("/scratch/shared/leone/krusemi/execslave/work/work4/run-test-suite/Performance/Polybench-421/linear-algebra/solvers/ludcmp/cmake_install.cmake")
  include("/scratch/shared/leone/krusemi/execslave/work/work4/run-test-suite/Performance/Polybench-421/linear-algebra/solvers/trisolv/cmake_install.cmake")

endif()

