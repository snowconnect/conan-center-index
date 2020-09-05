import os
from conans import ConanFile, tools, AutoToolsBuildEnvironment
from conans.errors import ConanInvalidConfiguration


class DarknetConan(ConanFile):
    name = "darknet"
    license = "YOLO"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "http://pjreddie.com/darknet/"
    description = "Darknet is a neural network frameworks written in C"
    topics = ("darknet", "neural network", "deep learning")
    settings = "os", "compiler", "build_type", "arch", "arch_build"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_opencv": [True, False]
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_opencv": False,
    }

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    @property
    def _commit(self):
        url = self.conan_data["sources"][self.version]["url"]
        return url[url.rfind("/")+1:url.rfind(".")]

    @property
    def _lib_to_compile(self):
        if not self.options.shared:
            return "$(ALIB)"
        else:
            return "$(SLIB)"

    @property
    def _shared_lib_extension(self):
        if self.settings.os == "Macos":
            return ".dylib"
        else:
            return ".so"

    def _patch_sources(self):
        tools.replace_in_file(os.path.join(self._source_subfolder, "Makefile"), "OPENCV=0", "OPENCV={}".format("1" if self.options.with_opencv else "0")

    def configure(self):
        if self.settings.os == "Windows":
            raise ConanInvalidConfiguration("This library is not compatible with Windows")
        del self.settings.compiler.libcxx
        del self.settings.compiler.cppstd

    def requirements(self):
        if self.options.with_opencv:
            # FIXME: opencv recipe is missing on CCI
            raise ConanInvalidConfiguration("opencv recipe is not (yet) available on CCI")

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        extracted_folder = self.name + "-" + self._commit
        os.rename(extracted_folder, self._source_subfolder)

    def build(self):
        self._activate_makefile("OpenCV")
        with tools.chdir(self._source_subfolder):
            tools.replace_in_file('Makefile', "-fPIC", "")
            tools.replace_in_file('Makefile', "CFLAGS=", "CFLAGS+=${CPPFLAGS} ")
            tools.replace_in_file('Makefile', "LDFLAGS=", "LDFLAGS+=${LIBS} ")
            tools.replace_in_file(
                'Makefile',
                "SLIB=libdarknet.so",
                "SLIB=libdarknet" + self._shared_lib_extension
            )
            tools.replace_in_file(
                'Makefile',
                "all: obj backup results $(SLIB) $(ALIB) $(EXEC)",
                "all: obj backup results " + self._lib_to_compile
            )
            env_build = AutoToolsBuildEnvironment(self)
            env_build.make()

    def package(self):
        self.copy("LICENSE*", dst="licenses", src=self._source_subfolder)
        self.copy("*.h", dst="include", src=os.path.join(self._source_subfolder, "include"))
        self.copy("*.so", dst="lib", keep_path=False)
        self.copy("*.dylib", dst="lib", keep_path=False)
        self.copy("*.a", dst="lib", keep_path=False)
        self.copy("*.lib", dst="lib", keep_path=False)

    def package_info(self):
        self.cpp_info.libs = ["darknet"]
        if self.settings.os == "Linux":
            self.cpp_info.system_libs = ["m", "pthread"]
