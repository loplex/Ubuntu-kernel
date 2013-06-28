#!/usr/bin/env python
#

from ktl.utils                          import error
import sys, os, re
common_lib = os.path.dirname(os.path.abspath(sys.argv[0]))
common_lib = os.path.dirname(common_lib)
common_lib = os.path.join(common_lib, "lib")
sys.path.insert(0, common_lib)
from buildenv_lib                       import GetUploadVersion

#
# CheckComponent
#
# This class uses the launchpad api to list components where packages
# landed or checking for their component mismatches. Intended to check
# kernel set packages, but can be extended or used with all packages
#
class CheckComponent():

    def __init__(s, lp):
        s.lp = lp
        # note: for package names with ABI in the name, replace the
        # number with the string 'ABI'
        s.release_db = {}
        s.abi_db = {}
        s.ubuntu = s.lp.launchpad.distributions["ubuntu"]
        s.main_archive = s.ubuntu.main_archive
        return

    def load_release_components(s, series, package):
        lp_series = s.ubuntu.getSeries(name_or_version=series)
        rel_ver = GetUploadVersion(series, package, pocket="release")
        if rel_ver:
            pkg_rel = s.main_archive.getPublishedSources(exact_match=True,
                        source_name=package,
                        distro_series=lp_series,
                        pocket='Release',
                        version=rel_ver)
            if pkg_rel:
                src_pkg = pkg_rel[0]
                s.release_db[package] = {}
                s.release_db[package][None] = src_pkg.component_name
                for bin_pkg in src_pkg.getPublishedBinaries():
                    bname = bin_pkg.binary_package_name
                    bcomponent = bin_pkg.component_name
                    s.release_db[package][bname] = bcomponent
        return

    def default_component(s, dcomponent, series, package, bin_pkg):
        if not s.release_db:
            s.load_release_components(series, package)
        if package in s.release_db:
            if bin_pkg in s.release_db[package]:
                return s.release_db[package][bin_pkg]
        return dcomponent

    def override_component(s, dcomponent, series, package, bin_pkg):
        if series != 'hardy' and package == 'linux-meta':
            if (bin_pkg and bin_pkg.startswith('linux-backports-modules-') and
                (not bin_pkg.endswith('-preempt'))):
                return 'main'
        return s.default_component(dcomponent, series, package, bin_pkg)

    def main_component(s, dcomponent, series, package, bin_pkg):
        return 'main'

    def name_abi_transform(s, name):
        if not name:
            return name
        abi = re.findall('([0-9]+\.[^ ]+)', name)
        if abi:
            abi = abi[0]
            abi = abi.split('-')
            if len(abi) >= 2:
                abi = abi[1]
            else:
                abi = None
            if abi:
                version = re.findall('([0-9]+\.[^-]+)', name)
                if version:
                    version = version[0]
                    name = name.replace('%s-%s' % (version, abi),
                                        '%s-ABI' % version)
        return name

    def linux_abi_component(s, dcomponent, series, package, bpkg):
        if package in s.abi_db:
            if package.startswith('linux-backports-modules-'):
                if not bpkg or not bpkg.endswith('-preempt'):
                    return 'main'
            return 'universe'

        lp_series = s.ubuntu.getSeries(name_or_version=series)
        rel_ver = GetUploadVersion(series, package, pocket="release")
        if rel_ver:
            pkg_rel = s.main_archive.getPublishedSources(exact_match=True,
                        source_name=package,
                        distro_series=lp_series,
                        pocket='Release',
                        version=rel_ver)
            if pkg_rel:
                src_pkg = pkg_rel[0]
                s.abi_db[package] = {}
                s.abi_db[package][None] = src_pkg.component_name
                for bin_pkg in src_pkg.getPublishedBinaries():
                    bname = s.name_abi_transform(bin_pkg.binary_package_name)
                    s.abi_db[package][bname] = bin_pkg.component_name
            else:
                s.abi_db[package] = {}
        else:
            s.abi_db[package] = {}
        return s.linux_abi_component(dcomponent, series, package, bpkg)

    def component_function(s, series, package):
        if (package == 'linux') or (package == 'linux-signed') or (package == 'linux-ppc'):
            # Everything on linux package should be on 'main'. Except
            # for hardy and lucid, where we had some things on universe
            # etc., so we use the linux_abi_component that will check
            # also where packages were on 'release' pocket
            if series in [ 'lucid' ]:
                return s.linux_abi_component
            return s.main_component
        if (package == 'linux-meta'):
            # Some precise meta packages were new and never released
            # originally, so they will default to 'universe' in the
            # checker. All of them should be on main anyway, so always
            # return 'main'
            if series in [ 'precise' ]:
                return s.main_component
            return s.override_component
        if package.startswith('linux-backports-modules-'):
            return s.linux_abi_component
        if (package.startswith('linux-lts-') or
            package.startswith('linux-meta-lts-') or
            package.startswith('linux-signed-lts-')):
            return s.main_component
        if package in ['linux-ec2', 'linux-ti-omap4', 'linux-armadaxp', 'linux-ppc']:
            return s.main_component

        return s.default_component

    def get_published_sources(s, series, package, version, pocket):
        if not version:
            version = GetUploadVersion(series, package, pocket=pocket)
            if not version:
                error("No upload of %s for %s is currently available in"
                      " the %s pocket" % (package, series, pocket))
                return None
        lp_series = s.ubuntu.getSeries(name_or_version=series)
        ps = s.main_archive.getPublishedSources(exact_match=True,
                                         source_name=package,
                                         distro_series=lp_series,
                                         pocket=pocket.title(),
                                         version=version)
        if not ps:
            error("No results returned by getPublishedSources")
        return ps

    def components_list(s, series, package, version, pocket, ps = None):
        clist = []
        if not ps:
            ps = s.get_published_sources(series, package, version, pocket)
        if ps:
            src_pkg = ps[0]
            clist.append([src_pkg.source_package_name,
                          src_pkg.source_package_version,
                          src_pkg.component_name])
            for bin_pkg in src_pkg.getPublishedBinaries():
                clist.append([bin_pkg.binary_package_name,
                              bin_pkg.binary_package_version,
                              bin_pkg.component_name])
        return clist

    def mismatches_list(s, series, package, version, pocket, ps = None):
        mlist = []
        s.release_db = {}
        s.abi_db = {}
        get_component = s.component_function(series, package)
        if not ps:
            ps = s.get_published_sources(series, package, version, pocket)
        if ps:
            src_pkg = ps[0]
            component = get_component('universe', series, package, None)
            if src_pkg.component_name != component:
                mlist.append([src_pkg.source_package_name,
                              src_pkg.source_package_version,
                              src_pkg.component_name, component])
            for bin_pkg in src_pkg.getPublishedBinaries():
                pkg_name = bin_pkg.binary_package_name
                component = get_component('universe', series, package, pkg_name)
                if bin_pkg.component_name != component:
                    mlist.append([bin_pkg.binary_package_name,
                                  bin_pkg.binary_package_version,
                                  bin_pkg.component_name, component])
        return mlist

# vi:set ts=4 sw=4 expandtab:
