<!-- #################################################################
<!-- /qompassai/.config/dkms/rapiddisk/log.md
<!-- Qompass AI Log
<!-- SPDX-License-Identifier: Apache-2.0
<!-- Copyright (c) 2026 Qompass AI
<!--
<!-- Licensed under the Apache License, Version 2.0 (the "License");
<!-- you may not use this file except in compliance with the License.
<!-- You may obtain a copy of the License at:
<!--   http://www.apache.org/licenses/LICENSE-2.0
<!--
<!-- Unless required by applicable law or agreed to in writing, software
<!-- distributed under the License is distributed on an "AS IS" BASIS,
<!-- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
<!-- See the License for the specific language governing permissions and
<!-- limitations under the License.
<!-- ################################################################# -->
[phaedrus@primo formatters]$ cat /var/lib/dkms/rapiddisk/9.1.0/build/make.log
DKMS (dkms-3.4.3) make.log for rapiddisk/9.1.0 for kernel 7.2.7-zen1-1-zen (x86_64)
Mon Sep 21 05:31:38 PM PDT 2026

Building module(s)
# command: make -j32 KERNELRELEASE=7.2.7-zen1-1-zen -C /usr/lib/modules/7.2.7-zen1-1-zen/build M=/var/lib/dkms/rapiddisk/9.1.0/build
make: Entering directory '/usr/lib/modules/7.2.7-zen1-1-zen/build'
make[1]: Entering directory '/var/lib/dkms/rapiddisk/9.1.0/build'
  CC [M]  rapiddisk.o
  CC [M]  rapiddisk-cache.o
rapiddisk-cache.c:166:5: warning: no previous prototype for ‘dm_io_async_bvec’ [-Wmissing-prototypes]
  166 | int dm_io_async_bvec(unsigned int num_regions, struct dm_io_region *where,
      |     ^~~~~~~~~~~~~~~~
rapiddisk-cache.c: In function ‘dm_io_async_bvec’:
rapiddisk-cache.c:198:16: error: too few arguments to function ‘dm_io’; expected 6, have 4
  198 |         return dm_io(&iorq, num_regions, where, NULL);
      |                ^~~~~
In file included from rapiddisk-cache.c:46:
/usr/lib/modules/7.2.7-zen1-1-zen/build/include/linux/dm-io.h:82:5: note: declared here
   82 | int dm_io(struct dm_io_request *io_req, unsigned int num_regions,
      |     ^~~~~
rapiddisk-cache.c: At top level:
rapiddisk-cache.c:253:6: warning: no previous prototype for ‘rc_io_callback’ [-Wmissing-prototypes]
  253 | void rc_io_callback(unsigned long error, void *context)
      |      ^~~~~~~~~~~~~~
In file included from /usr/lib/modules/7.2.7-zen1-1-zen/build/include/linux/build_bug.h:5,
                 from /usr/lib/modules/7.2.7-zen1-1-zen/build/include/linux/init.h:5,
                 from rapiddisk.c:26:
rapiddisk.c: In function ‘rdsk_lookup_page’:
rapiddisk.c:252:28: error: ‘struct page’ has no member named ‘index’
  252 |         BUG_ON(page && page->index != idx);
      |                            ^~
/usr/lib/modules/7.2.7-zen1-1-zen/build/include/linux/compiler.h:77:45: note: in definition of macro ‘unlikely’
   77 | # define unlikely(x)    __builtin_expect(!!(x), 0)
      |                                             ^
rapiddisk.c:252:9: note: in expansion of macro ‘BUG_ON’
  252 |         BUG_ON(page && page->index != idx);
      |         ^~~~~~
rapiddisk-cache.c: In function ‘do_io’:
rapiddisk-cache.c:361:58: error: passing argument 5 of ‘dm_io_async_bvec’ from incompatible pointer type [-Wincompatible-pointer-types]
  361 |         r = dm_io_async_bvec(1, &job->cache, WRITE, bio, rc_io_callback, job);
      |                                                          ^~~~~~~~~~~~~~
      |                                                          |
      |                                                          void (*)(long unsigned int,  void *)
rapiddisk-cache.c:168:60: note: expected ‘io_notify_fn’ {aka ‘void (*)(long unsigned int,  long unsigned int,  void *)’} but argument is of type ‘void (*)(long unsigned int,  void *)’
  168 |                      int rw, struct bio *bio, io_notify_fn fn, void *context)
      |                                               ~~~~~~~~~~~~~^~
rapiddisk-cache.c:253:6: note: ‘rc_io_callback’ declared here
  253 | void rc_io_callback(unsigned long error, void *context)
      |      ^~~~~~~~~~~~~~
/usr/lib/modules/7.2.7-zen1-1-zen/build/include/linux/dm-io.h:30:16: note: ‘io_notify_fn’ declared here
   30 | typedef void (*io_notify_fn)(unsigned long int error, unsigned long int unsup, void *context);
      |                ^~~~~~~~~~~~
rapiddisk.c: In function ‘rdsk_insert_page’:
rapiddisk.c:288:13: error: ‘struct page’ has no member named ‘index’
  288 |         page->index = idx;
      |             ^~
rapiddisk-cache.c: At top level:
rapiddisk-cache.c:369:5: warning: no previous prototype for ‘rc_do_complete’ [-Wmissing-prototypes]
  369 | int rc_do_complete(struct kcached_job *job)
      |     ^~~~~~~~~~~~~~
rapiddisk.c:293:28: error: ‘struct page’ has no member named ‘index’
  293 |                 BUG_ON(page->index != idx);
      |                            ^~
/usr/lib/modules/7.2.7-zen1-1-zen/build/include/linux/compiler.h:77:45: note: in definition of macro ‘unlikely’
   77 | # define unlikely(x)    __builtin_expect(!!(x), 0)
      |                                             ^
rapiddisk.c:293:17: note: in expansion of macro ‘BUG_ON’
  293 |                 BUG_ON(page->index != idx);
      |                 ^~~~~~
rapiddisk-cache.c:411:6: warning: no previous prototype for ‘kcached_client_destroy’ [-Wmissing-prototypes]
  411 | void kcached_client_destroy(struct cache_context *dmc)
      |      ^~~~~~~~~~~~~~~~~~~~~~
rapiddisk.c: In function ‘rdsk_free_pages’:
rapiddisk.c:332:40: error: ‘struct page’ has no member named ‘index’
  332 |                         BUG_ON(pages[i]->index < pos);
      |                                        ^~
/usr/lib/modules/7.2.7-zen1-1-zen/build/include/linux/compiler.h:77:45: note: in definition of macro ‘unlikely’
   77 | # define unlikely(x)    __builtin_expect(!!(x), 0)
      |                                             ^
rapiddisk.c:332:25: note: in expansion of macro ‘BUG_ON’
  332 |                         BUG_ON(pages[i]->index < pos);
      |                         ^~~~~~
rapiddisk.c:333:39: error: ‘struct page’ has no member named ‘index’
  333 |                         pos = pages[i]->index;
      |                                       ^~
rapiddisk-cache.c: In function ‘cache_read_miss’:
rapiddisk-cache.c:592:39: error: passing argument 5 of ‘dm_io_async_bvec’ from incompatible pointer type [-Wincompatible-pointer-types]
  592 |                                  bio, rc_io_callback, job);
      |                                       ^~~~~~~~~~~~~~
      |                                       |
      |                                       void (*)(long unsigned int,  void *)
rapiddisk-cache.c:168:60: note: expected ‘io_notify_fn’ {aka ‘void (*)(long unsigned int,  long unsigned int,  void *)’} but argument is of type ‘void (*)(long unsigned int,  void *)’
  168 |                      int rw, struct bio *bio, io_notify_fn fn, void *context)
      |                                               ~~~~~~~~~~~~~^~
rapiddisk-cache.c:253:6: note: ‘rc_io_callback’ declared here
  253 | void rc_io_callback(unsigned long error, void *context)
      |      ^~~~~~~~~~~~~~
/usr/lib/modules/7.2.7-zen1-1-zen/build/include/linux/dm-io.h:30:16: note: ‘io_notify_fn’ declared here
   30 | typedef void (*io_notify_fn)(unsigned long int error, unsigned long int unsup, void *context);
      |                ^~~~~~~~~~~~
rapiddisk-cache.c: In function ‘cache_read’:
rapiddisk-cache.c:642:42: error: passing argument 5 of ‘dm_io_async_bvec’ from incompatible pointer type [-Wincompatible-pointer-types]
  642 |                                          rc_io_callback, job);
      |                                          ^~~~~~~~~~~~~~
      |                                          |
      |                                          void (*)(long unsigned int,  void *)
rapiddisk-cache.c:168:60: note: expected ‘io_notify_fn’ {aka ‘void (*)(long unsigned int,  long unsigned int,  void *)’} but argument is of type ‘void (*)(long unsigned int,  void *)’
  168 |                      int rw, struct bio *bio, io_notify_fn fn, void *context)
      |                                               ~~~~~~~~~~~~~^~
rapiddisk-cache.c:253:6: note: ‘rc_io_callback’ declared here
  253 | void rc_io_callback(unsigned long error, void *context)
      |      ^~~~~~~~~~~~~~
/usr/lib/modules/7.2.7-zen1-1-zen/build/include/linux/dm-io.h:30:16: note: ‘io_notify_fn’ declared here
   30 | typedef void (*io_notify_fn)(unsigned long int error, unsigned long int unsup, void *context);
      |                ^~~~~~~~~~~~
rapiddisk-cache.c: In function ‘cache_write’:
rapiddisk-cache.c:796:53: error: passing argument 5 of ‘dm_io_async_bvec’ from incompatible pointer type [-Wincompatible-pointer-types]
  796 |         dm_io_async_bvec(1, &job->disk, WRITE, bio, rc_io_callback, job);
      |                                                     ^~~~~~~~~~~~~~
      |                                                     |
      |                                                     void (*)(long unsigned int,  void *)
rapiddisk-cache.c:168:60: note: expected ‘io_notify_fn’ {aka ‘void (*)(long unsigned int,  long unsigned int,  void *)’} but argument is of type ‘void (*)(long unsigned int,  void *)’
  168 |                      int rw, struct bio *bio, io_notify_fn fn, void *context)
      |                                               ~~~~~~~~~~~~~^~
rapiddisk-cache.c:253:6: note: ‘rc_io_callback’ declared here
  253 | void rc_io_callback(unsigned long error, void *context)
      |      ^~~~~~~~~~~~~~
/usr/lib/modules/7.2.7-zen1-1-zen/build/include/linux/dm-io.h:30:16: note: ‘io_notify_fn’ declared here
   30 | typedef void (*io_notify_fn)(unsigned long int error, unsigned long int unsup, void *context);
      |                ^~~~~~~~~~~~
rapiddisk-cache.c: At top level:
rapiddisk-cache.c:819:5: warning: no previous prototype for ‘rc_map’ [-Wmissing-prototypes]
  819 | int rc_map(struct dm_target *ti, struct bio *bio)
      |     ^~~~~~
rapiddisk.c: In function ‘attach_device’:
rapiddisk.c:809:61: error: macro ‘blk_alloc_disk’ requires 2 arguments, but only 1 given
  809 |         disk = rdsk->rdsk_disk = blk_alloc_disk(NUMA_NO_NODE);
      |                                                             ^
In file included from rapiddisk.c:30:
/usr/lib/modules/7.2.7-zen1-1-zen/build/include/linux/blkdev.h:997:9: note: macro ‘blk_alloc_disk’ defined here
  997 | #define blk_alloc_disk(lim, node_id)                                    \
      |         ^~~~~~~~~~~~~~
rapiddisk.c:809:34: error: ‘blk_alloc_disk’ undeclared (first use in this function)
  809 |         disk = rdsk->rdsk_disk = blk_alloc_disk(NUMA_NO_NODE);
      |                                  ^~~~~~~~~~~~~~
rapiddisk.c:809:34: note: ‘blk_alloc_disk’ is a function-like macro and might be used incorrectly
rapiddisk.c:809:34: note: each undeclared identifier is reported only once for each function it appears in
rapiddisk.c:816:61: error: macro ‘blk_alloc_disk’ requires 2 arguments, but only 1 given
  816 |         disk = rdsk->rdsk_disk = blk_alloc_disk(NUMA_NO_NODE);
      |                                                             ^
/usr/lib/modules/7.2.7-zen1-1-zen/build/include/linux/blkdev.h:997:9: note: macro ‘blk_alloc_disk’ defined here
  997 | #define blk_alloc_disk(lim, node_id)                                    \
      |         ^~~~~~~~~~~~~~
rapiddisk-cache.c: In function ‘rc_start_uncached_io’:
rapiddisk-cache.c:919:31: error: passing argument 5 of ‘dm_io_async_bvec’ from incompatible pointer type [-Wincompatible-pointer-types]
  919 |                          bio, rc_uncached_io_callback, job);
      |                               ^~~~~~~~~~~~~~~~~~~~~~~
      |                               |
      |                               void (*)(long unsigned int,  void *)
rapiddisk-cache.c:168:60: note: expected ‘io_notify_fn’ {aka ‘void (*)(long unsigned int,  long unsigned int,  void *)’} but argument is of type ‘void (*)(long unsigned int,  void *)’
  168 |                      int rw, struct bio *bio, io_notify_fn fn, void *context)
      |                                               ~~~~~~~~~~~~~^~
rapiddisk-cache.c:861:13: note: ‘rc_uncached_io_callback’ declared here
  861 | static void rc_uncached_io_callback(unsigned long error, void *context)
      |             ^~~~~~~~~~~~~~~~~~~~~~~
/usr/lib/modules/7.2.7-zen1-1-zen/build/include/linux/dm-io.h:30:16: note: ‘io_notify_fn’ declared here
   30 | typedef void (*io_notify_fn)(unsigned long int error, unsigned long int unsup, void *context);
      |                ^~~~~~~~~~~~
rapiddisk-cache.c: In function ‘rc_get_dev’:
rapiddisk-cache.c:941:17: error: implicit declaration of function ‘strncpy’ [-Wimplicit-function-declaration]
  941 |                 strncpy(dmc_dname, pth, DEV_PATHLEN);
      |                 ^~~~~~~
rapiddisk-cache.c:48:1: note: include ‘<string.h>’ or provide a declaration of ‘strncpy’
   47 | #include <linux/device-mapper.h>
  +++ |+#include <string.h>
   48 | 
rapiddisk-cache.c:941:17: warning: incompatible implicit declaration of built-in function ‘strncpy’ [-Wbuiltin-declaration-mismatch]
  941 |                 strncpy(dmc_dname, pth, DEV_PATHLEN);
      |                 ^~~~~~~
rapiddisk-cache.c:941:17: note: include ‘<string.h>’ or provide a declaration of ‘strncpy’
rapiddisk-cache.c: In function ‘cache_ctr’:
rapiddisk-cache.c:1022:59: error: ‘struct block_device’ has no member named ‘bd_inode’
 1022 |                 dmc->size = to_sector(dmc->cache_dev->bdev->bd_inode->i_size);
      |                                                           ^~
rapiddisk-cache.c:1058:50: error: ‘struct block_device’ has no member named ‘bd_inode’
 1058 |         dev_size = to_sector(dmc->cache_dev->bdev->bd_inode->i_size);
      |                                                  ^~
rapiddisk-cache.c: At top level:
rapiddisk-cache.c:1259:12: warning: no previous prototype for ‘rc_init’ [-Wmissing-prototypes]
 1259 | int __init rc_init(void)
      |            ^~~~~~~
rapiddisk-cache.c:1279:6: warning: no previous prototype for ‘rc_exit’ [-Wmissing-prototypes]
 1279 | void rc_exit(void)
      |      ^~~~~~~
make[3]: *** [/usr/lib/modules/7.2.7-zen1-1-zen/build/scripts/Makefile.build:289: rapiddisk-cache.o] Error 1
make[3]: *** Waiting for unfinished jobs....
rapiddisk.c:823:9: error: implicit declaration of function ‘blk_queue_logical_block_size’; did you mean ‘queue_logical_block_size’? [-Wimplicit-function-declaration]
  823 |         blk_queue_logical_block_size(disk->queue, BYTES_PER_SECTOR);
      |         ^~~~~~~~~~~~~~~~~~~~~~~~~~~~
      |         queue_logical_block_size
rapiddisk.c:824:9: error: implicit declaration of function ‘blk_queue_physical_block_size’; did you mean ‘queue_physical_block_size’? [-Wimplicit-function-declaration]
  824 |         blk_queue_physical_block_size(disk->queue, PAGE_SIZE);
      |         ^~~~~~~~~~~~~~~~~~~~~~~~~~~~~
      |         queue_physical_block_size
rapiddisk.c:831:9: error: too many arguments to function ‘blk_queue_write_cache’; expected 1, have 3
  831 |         blk_queue_write_cache(disk->queue, false, false);
      |         ^~~~~~~~~~~~~~~~~~~~~              ~~~~~
/usr/lib/modules/7.2.7-zen1-1-zen/build/include/linux/blkdev.h:1502:20: note: declared here
 1502 | static inline bool blk_queue_write_cache(struct request_queue *q)
      |                    ^~~~~~~~~~~~~~~~~~~~~
rapiddisk.c:847:9: error: implicit declaration of function ‘blk_queue_max_discard_sectors’; did you mean ‘bdev_max_discard_sectors’? [-Wimplicit-function-declaration]
  847 |         blk_queue_max_discard_sectors(disk->queue, 0);
      |         ^~~~~~~~~~~~~~~~~~~~~~~~~~~~~
      |         bdev_max_discard_sectors
rapiddisk.c:851:28: error: ‘QUEUE_FLAG_NONROT’ undeclared (first use in this function); did you mean ‘QUEUE_FLAG_NOMERGES’?
  851 |         blk_queue_flag_set(QUEUE_FLAG_NONROT, disk->queue);
      |                            ^~~~~~~~~~~~~~~~~
      |                            QUEUE_FLAG_NOMERGES
make[3]: *** [/usr/lib/modules/7.2.7-zen1-1-zen/build/scripts/Makefile.build:289: rapiddisk.o] Error 1
make[2]: *** [/usr/lib/modules/7.2.7-zen1-1-zen/build/Makefile:2201: .] Error 2
make[1]: *** [/usr/lib/modules/7.2.7-zen1-1-zen/build/Makefile:248: __sub-make] Error 2
make[1]: Leaving directory '/var/lib/dkms/rapiddisk/9.1.0/build'
make: *** [Makefile:248: __sub-make] Error 2
make: Leaving directory '/usr/lib/modules/7.2.7-zen1-1-zen/build'

# exit code: 2
# elapsed time: 00:00:00
----------------------------------------------------------------
[phaedrus@primo formatters]$ 
