import subprocess as sp
import multiprocessing as mp
import argparse
import os
import sys

gcc_opt = "-Ofast"

env_tpl = '''
#!/bin/bash
if [[ ! -z "$NF_MODULES_LOADED" ]]
then
  module load gcc/9.1.0
  module load autotools/20170329
  module load libtool/2.4.6
  module load perl/5.22.1
fi

set -xeu

prefix="{prefix}"
export PKG_CONFIG_PATH=$prefix/lib/pkgconfig
export PATH="$prefix/bin:$PATH"
export LD_LIBRARY_PATH="$prefix/lib"
export CPPFLAGS="%s -I$prefix/include"
export CXXFLAGS="%s -I$prefix/include"
export CFLAGS="%s -I$prefix/include"
export LDFLAGS=-L$prefix/lib

''' % (gcc_opt, gcc_opt, gcc_opt)

def build_cmd_tpl(dep_name, conf='', env=''):
  return '''
[[ -f "{prefix}/%s" ]] || (
%s
%s
rm -rf {src_dir}
mkdir -p {src_dir}
tar -xf {filename} --strip-components=1 -C {src_dir} && cd {src_dir}
./configure --prefix="{prefix}" %s && make -s -j{n_jobs} install
) 
''' % (dep_name, env_tpl, env, conf)

deps = {
  'pkg-config-0.29.tar.gz': ['https://pkgconfig.freedesktop.org/releases/pkg-config-0.29.tar.gz',
    '''
    which pkg-config || [[ -f "{prefix}/bin/pkg-config" ]] || (
    %s
    rm -rf {src_dir}
    mkdir -p {src_dir}
    tar -xf {filename} --strip-components=1 -C {src_dir} && cd {src_dir}
    make -s -j{n_jobs}
    make -s install
    )
    ''' % env_tpl
  ],

  'cmake-3.15.0.tar.gz': ['https://github.com/Kitware/CMake/releases/download/v3.15.0/cmake-3.15.0.tar.gz',
    '''
    [[ -f "{prefix}/bin/cmake" ]] || (
    %s
    rm -rf {src_dir}
    mkdir -p {src_dir}
    tar -xf {filename} --strip-components=1 -C {src_dir} && cd {src_dir}
    ./bootstrap --prefix="{prefix}" --parallel={n_jobs}
    make -s -j{n_jobs}
    make -s install
    )
    ''' % env_tpl
  ],

  'zlib-1.2.11': ['https://zlib.net/zlib-1.2.11.tar.gz',
    build_cmd_tpl('lib/libz.so')
  ],

  'openssl-1.1.1': ['https://github.com/openssl/openssl/archive/OpenSSL_1_1_1c.tar.gz',
    '''
    [[ -f "{prefix}/lib/libssl.so" ]] || (
    %s
    rm -rf {src_dir}
    mkdir -p {src_dir}
    tar -xf {filename} --strip-components=1 -C {src_dir} && cd {src_dir}
    ./config --prefix="{prefix}" --openssldir="{prefix}" shared zlib
    make -s -j{n_jobs}
    make -s install
    )
    ''' % env_tpl
  ],

  'curl-7.65.1': ['https://github.com/curl/curl/releases/download/curl-7_65_1/curl-7.65.1.tar.gz',
    '''
    [[ -f "{prefix}/lib/libcurl.so" ]] || (
    %s
    rm -rf {src_dir}
    mkdir -p {src_dir}
    tar -xf {filename} --strip-components=1 -C {src_dir} && cd {src_dir}
    ./buildconf
    ./configure --prefix="{prefix}" --with-ssl="{prefix}"
    make -s -j{n_jobs} install
    )
    ''' % env_tpl
  ],

  'sqlite3.29.tar.gz': ['http://ftp.osuosl.org/pub/blfs/conglomeration/sqlite/sqlite-autoconf-3290000.tar.gz',
    build_cmd_tpl('lib/libsqlite3.so', '--disable-tcl --enable-fts5 --enable-json1 --enable-update-limit --enable-rtree --enable-mesys5 --enable-tempstore --enable-releasemode --enable-geopoly')
  ],

  'jpeg-9c.tar.gz': ['http://www.ijg.org/files/jpegsrc.v9c.tar.gz',
    build_cmd_tpl('lib/libjpeg.so')
  ],

  'openjpeg-2.3.1.tar.gz': ['https://github.com/uclouvain/openjpeg/archive/v2.3.1.tar.gz',
    '''
    [[ -f "{prefix}/lib/libopenjp2.so" ]] || (
    %s
    rm -rf {src_dir}
    mkdir -p {src_dir}
    tar -xf {filename} --strip-components=1 -C {src_dir} && cd {src_dir}
    mkdir build
    cd build
    cmake .. -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="{prefix}"
    make -s -j{n_jobs}
    make -s install
    )
    ''' % env_tpl
  ],

  'geos-3.7.2.tar.gz': ['https://github.com/libgeos/geos/archive/3.7.2.tar.gz',
    '''
    [[ -f "{prefix}/lib/libgeos.so" ]] || (
    %s
    rm -rf {src_dir}
    mkdir -p {src_dir}
    tar -xf {filename} --strip-components=1 -C {src_dir} && cd {src_dir}
    ./autogen.sh
    ./configure --prefix="{prefix}" && make -s -j{n_jobs} install
    )
    ''' % (env_tpl)
  ],

  'proj-6.1.1.tar.gz': ['https://github.com/OSGeo/PROJ/releases/download/6.1.1/proj-6.1.1.tar.gz',
    build_cmd_tpl('lib/libproj.so', env='''
     export SQLITE3_CFLAGS="-I$prefix/include"
     export SQLITE3_LIBS="-L$prefix/lib -lsqlite3"
    ''')
  ],

  'hdf-4.2.13.tar.gz': ['https://support.hdfgroup.org/ftp/HDF/HDF_Current/src/hdf-4.2.13.tar.gz',
    build_cmd_tpl('lib/libdf.so', '--enable-shared --disable-fortran')
  ],

  'hdf5-1.10.5.tar.gz': ['https://github.com/live-clones/hdf5/archive/hdf5-1_10_5.tar.gz',
    build_cmd_tpl('lib/libhdf5.so', '--enable-shared --enable-hl')
  ],

  'netcdf-c-4.7.0.tar.gz': ['https://github.com/Unidata/netcdf-c/archive/v4.7.0.tar.gz',
    build_cmd_tpl('lib/libnetcdf.so', '--enable-netcdf-4 --enable-shared --enable-dap --with-max-default-cache-size=67108864 --with-chunk-cache-size=67108864', env='''
      export CFLAGS="%s -DHAVE_STRDUP -I$prefix/include"
    ''' % gcc_opt)
  ],

  'libxml2-2.9.8.tar.gz': ['ftp://xmlsoft.org/libxml2/libxml2-2.9.8.tar.gz',
    build_cmd_tpl('lib/libxml2.so', '--without-python')
  ],

  'json-c-0.13.1.tar.gz': ['https://s3.amazonaws.com/json-c_releases/releases/json-c-0.13.1.tar.gz',
    build_cmd_tpl('lib/libjson-c.so')
  ],

  'llvm-8.0.1.tar.gz': ['https://github.com/llvm/llvm-project/archive/llvmorg-8.0.1.tar.gz',
     '''
    [[ -f "{prefix}/bin/llvm-config" ]] || (
    %s
    rm -rf {src_dir}
    mkdir -p {src_dir}
    tar -xf {filename} --strip-components=1 -C {src_dir} && cd {src_dir}
    mkdir build && cd build
    cmake -G"Unix Makefiles" -DLLVM_TEMPORARILY_ALLOW_OLD_TOOLCHAIN=1 -DCMAKE_INSTALL_PREFIX="{prefix}" -DLLVM_ENABLE_PROJECTS=clang -DCMAKE_BUILD_TYPE=Release ../llvm
    make -s -j{n_jobs} install
    )
    ''' % (env_tpl)
  ],

  'postgresql-12.tar.gz': ['https://ftp.postgresql.org/pub/source/v12beta2/postgresql-12beta2.tar.gz',
    build_cmd_tpl('bin/pg_config', '--with-python --with-libxml --without-readline --with-llvm LLVM_CONFIG="{prefix}/bin/llvm-config"', env='''
      export CFLAGS="-O2 -I$prefix/include"
      export CPPFLAGS="-O2 -I$prefix/include"
    ''')
  ],

  'gdal-3.0.1.tar.gz': ['https://github.com/OSGeo/gdal/archive/v3.0.1.tar.gz',
    '''
    [[ -f "{prefix}/lib/libgdal.so" ]] || (
    %s
    rm -rf {src_dir}
    mkdir -p {src_dir}
    tar -xf {filename} --strip-components=1 -C {src_dir} && cd {src_dir}/gdal
    ./autogen.sh
    ./configure --prefix="{prefix}" --with-geos=yes --with-netcdf --with-sfcgal=no --with-libjson-c={prefix} && make -s -j{n_jobs} install
    )
    ''' % (env_tpl)
  ],

  'postgis-3.0.0.tar.gz': ['https://github.com/postgis/postgis/archive/3.0.0alpha3.tar.gz',
    '''
    [[ -f "{prefix}/lib/postgresql/postgis-3.so" ]] || (
    %s
    rm -rf {src_dir}
    mkdir -p {src_dir}
    tar -xf {filename} --strip-components=1 -C {src_dir} && cd {src_dir}
    ./autogen.sh
    ./configure --prefix="{prefix}" --with-sfcgal=no && make -s -j{n_jobs} install
    )
    ''' % (env_tpl)
  ],

}

def download_deps(args):
  if not os.path.exists(args.download_dir):
    os.makedirs(args.download_dir)

  has_wget = False
  try:
    sp.check_output('which wget', shell=True)
    has_wget = True
  except:
    pass
  for pkg, info in deps.items():
    url = info[0]
    out_filename = os.path.join(args.download_dir, pkg)
    if not os.path.exists(out_filename):
      if has_wget:
        cmd = 'set -xeu; wget -q -O %s %s' % (out_filename, url)
      else:
        cmd = 'set -xeu; curl %s -s -L -o %s' % (url, out_filename)
      sp.check_output(cmd, shell=True)

def build_deps(args):
  build_prefix = os.path.abspath(args.build_dir)

  if not os.path.exists(build_prefix):
    os.makedirs(build_prefix)

  python_bin = os.path.abspath(args.python_bin)
  python_link_dir = os.path.join(build_prefix, 'bin')
  python_link = os.path.join(python_link_dir, 'python')
  if not os.path.exists(python_link):
    if not os.path.exists(python_link_dir):
      os.makedirs(python_link_dir)
    cmd = 'set -xeu;ln -s %s %s/python' % (python_bin, python_link_dir)
    sp.run(cmd, stdout=sys.stdout, stderr=sys.stderr, shell=True, check=True)

  for pkg, info in deps.items():
    pkg_filename = os.path.join(args.download_dir, pkg)
    src_dir_name = pkg[:len(pkg)-len('.tar.gz')]
    src_dir = os.path.join(build_prefix, 'deps_src', src_dir_name)

    build_cmd = info[1]
    build_cmd = build_cmd.format(filename=pkg_filename, src_dir=src_dir, prefix=build_prefix, n_jobs=args.n_jobs)
    sp.run(build_cmd, stdout=sys.stdout, stderr=sys.stderr, shell=True, check=True)

def build_gsky(args):
  build_prefix = os.path.abspath(args.build_dir)
  env = env_tpl.format(prefix=build_prefix)
  build_cmd = '''
      %s
      export CGO_LDFLAGS=$LDFLAGS 
      export CGO_CFLAGS=$CFLAGS 

      C_INCLUDE_PATH=$(nc-config --includedir)
      export C_INCLUDE_PATH

      [[ -f $prefix/go/bin/go ]] || (set -xeu
      v=1.12.7
      rm -rf go.tar.gz
      wget -q -O go.tar.gz https://dl.google.com/go/go${v}.linux-amd64.tar.gz
      tar -xf go.tar.gz
      rm -rf go.tar.gz
      rm -rf $prefix/go
      mv go $prefix/go
      )

      export GOROOT=$prefix/go
      export GOPATH=$prefix/gopath
      export PATH="$GOROOT/bin:$PATH"

      mkdir -p $GOPATH

#      rm -rf $GOPATH/src/github.com/nci/gsky
#      git clone https://github.com/nci/gsky.git $GOPATH/src/github.com/nci/gsky

      (set -exu
      cd $GOPATH/src/github.com/nci/gsky

      ./configure
      make all
      )

      rm -rf $prefix/share/gsky
      rm -rf $prefix/share/mas

      mkdir -p $prefix/share/gsky
      mkdir -p $prefix/share/mas

      cp -rf $GOPATH/src/github.com/nci/gsky/concurrent $prefix/bin/concurrent
      cp -rf $GOPATH/src/github.com/nci/gsky/*.so $prefix/share/gsky/
      cp -rf $GOPATH/bin/api $prefix/share/gsky/masapi
      cp -rf $GOPATH/bin/gsky $prefix/share/gsky/ows
      cp -rf $GOPATH/bin/grpc-server $prefix/share/gsky/grpc_server
      cp -rf $GOPATH/bin/gdal-process $prefix/share/gsky/gsky-gdal-process
      cp -rf $GOPATH/bin/crawl $prefix/share/gsky/gsky-crawl
      cp -rf $GOPATH/src/github.com/nci/gsky/crawl/crawl_pipeline.sh $prefix/share/gsky/crawl_pipeline.sh
      cp -rf $GOPATH/src/github.com/nci/gsky/mas/db/* $prefix/share/mas/
      cp -rf $GOPATH/src/github.com/nci/gsky/mas/api/*.sql $prefix/share/mas/

      cp -rf $GOPATH/src/github.com/nci/gsky/*.png $prefix/share/gsky/
      cp -rf $GOPATH/src/github.com/nci/gsky/templates $prefix/share/gsky/
      cp -rf $GOPATH/src/github.com/nci/gsky/static $prefix/share/gsky/
      ''' % env

  sp.run(build_cmd, stdout=sys.stdout, stderr=sys.stderr, shell=True, check=True)

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument('--download_dir', default='deps_download')
  parser.add_argument('--download_only', type=bool, default=False)
  parser.add_argument('--build_dir', default='gsky')
  parser.add_argument('--n_jobs', type=int, default=-1)
  parser.add_argument('--python_bin', default=sys.executable)
  args = parser.parse_args()

  assert sys.version_info[0] >= 3 and sys.version_info[1] >= 7

  if args.n_jobs <= 0:
    n_cpus = len(os.sched_getaffinity(0))
    args.n_jobs = n_cpus

  download_deps(args)
  if not args.download_only:
    build_deps(args)
    build_gsky(args)
