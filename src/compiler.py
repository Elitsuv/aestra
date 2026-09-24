from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar


class CompilationError(Exception):
    """Raised when compilation of a source file fails."""

    def __init__(self, message: str, stdout: str = "", stderr: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.stdout = stdout
        self.stderr = stderr


@dataclass(frozen=True)
class CompilationResult:
    """Represents the outcome of a compilation or cache lookup."""

    success: bool
    executable_path: Path
    cached: bool
    stdout: str = ""
    stderr: str = ""


class CompilerManager:
    """Detects system compilers, builds source files with CP flags, and caches output."""

    BUILD_DIR = Path(".aestra") / "build"

    CPP_EXTENSIONS: ClassVar[frozenset[str]] = frozenset({".cpp", ".cc", ".cxx"})
    C_EXTENSIONS: ClassVar[frozenset[str]] = frozenset({".c"})
    RUST_EXTENSIONS: ClassVar[frozenset[str]] = frozenset({".rs"})
    GO_EXTENSIONS: ClassVar[frozenset[str]] = frozenset({".go"})
    PYTHON_EXTENSIONS: ClassVar[frozenset[str]] = frozenset({".py"})

    SOURCE_EXTENSIONS: ClassVar[frozenset[str]] = (
        CPP_EXTENSIONS | C_EXTENSIONS | RUST_EXTENSIONS | GO_EXTENSIONS
    )

    @classmethod
    def is_source_file(cls, path: Path) -> bool:
        """Returns True if the file extension is a compilable source code file."""
        return path.suffix.lower() in cls.SOURCE_EXTENSIONS

    @classmethod
    def get_source_hash(cls, source_path: Path) -> str:
        """Computes a SHA-256 hash of the file contents for build cache validation."""
        hasher = hashlib.sha256()
        with open(source_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()[:16]

    @classmethod
    def prepare(cls, target_path: str | Path) -> CompilationResult:
        """Resolves target_path to an executable binary, compiling source files if necessary."""
        path = Path(target_path).resolve()

        if not path.exists():
            raise FileNotFoundError(f"Target file '{path}' does not exist.")

        # Non-source files (e.g., Python scripts or pre-compiled binaries) pass through
        if not cls.is_source_file(path):
            return CompilationResult(
                success=True,
                executable_path=path,
                cached=True,
            )

        suffix = path.suffix.lower()
        if suffix in cls.CPP_EXTENSIONS:
            return cls._compile_cpp(path)
        elif suffix in cls.C_EXTENSIONS:
            return cls._compile_c(path)
        elif suffix in cls.RUST_EXTENSIONS:
            return cls._compile_rust(path)
        elif suffix in cls.GO_EXTENSIONS:
            return cls._compile_go(path)

        raise CompilationError(f"Unsupported source extension: {suffix}")

    @classmethod
    def _get_output_binary_path(cls, source_path: Path, source_hash: str) -> Path:
        cls.BUILD_DIR.mkdir(parents=True, exist_ok=True)
        ext = ".exe" if sys.platform == "win32" else ""
        binary_name = f"{source_path.stem}_{source_hash}{ext}"
        return cls.BUILD_DIR / binary_name

    @classmethod
    def _compile_cpp(cls, source_path: Path) -> CompilationResult:
        source_hash = cls.get_source_hash(source_path)
        out_path = cls._get_output_binary_path(source_path, source_hash)

        if (
            out_path.exists()
            and out_path.stat().st_mtime >= source_path.stat().st_mtime
        ):
            return CompilationResult(
                success=True, executable_path=out_path, cached=True
            )

        compiler = shutil.which("g++") or shutil.which("clang++")
        if not compiler:
            raise CompilationError(
                "Neither 'g++' nor 'clang++' was found on your system PATH. "
                "Please install a C++ compiler to test .cpp files."
            )

        cmd = [
            compiler,
            "-O3",
            "-std=c++20",
            "-Wall",
            str(source_path),
            "-o",
            str(out_path),
        ]
        return cls._run_compiler_command(cmd, out_path)

    @classmethod
    def _compile_c(cls, source_path: Path) -> CompilationResult:
        source_hash = cls.get_source_hash(source_path)
        out_path = cls._get_output_binary_path(source_path, source_hash)

        if (
            out_path.exists()
            and out_path.stat().st_mtime >= source_path.stat().st_mtime
        ):
            return CompilationResult(
                success=True, executable_path=out_path, cached=True
            )

        compiler = shutil.which("gcc") or shutil.which("clang")
        if not compiler:
            raise CompilationError(
                "Neither 'gcc' nor 'clang' was found on your system PATH."
            )

        cmd = [
            compiler,
            "-O3",
            "-Wall",
            str(source_path),
            "-o",
            str(out_path),
        ]
        return cls._run_compiler_command(cmd, out_path)

    @classmethod
    def _compile_rust(cls, source_path: Path) -> CompilationResult:
        source_hash = cls.get_source_hash(source_path)
        out_path = cls._get_output_binary_path(source_path, source_hash)

        if (
            out_path.exists()
            and out_path.stat().st_mtime >= source_path.stat().st_mtime
        ):
            return CompilationResult(
                success=True, executable_path=out_path, cached=True
            )

        compiler = shutil.which("rustc")
        if not compiler:
            raise CompilationError(
                "'rustc' was not found on your system PATH. "
                "Please install the Rust toolchain (https://rustup.rs) to test .rs files."
            )

        cmd = [compiler, "-O", str(source_path), "-o", str(out_path)]
        return cls._run_compiler_command(cmd, out_path)

    @classmethod
    def _compile_go(cls, source_path: Path) -> CompilationResult:
        source_hash = cls.get_source_hash(source_path)
        out_path = cls._get_output_binary_path(source_path, source_hash)

        if (
            out_path.exists()
            and out_path.stat().st_mtime >= source_path.stat().st_mtime
        ):
            return CompilationResult(
                success=True, executable_path=out_path, cached=True
            )

        compiler = shutil.which("go")
        if not compiler:
            raise CompilationError(
                "'go' was not found on your system PATH. "
                "Please install Go (https://go.dev) to test .go files."
            )

        cmd = [compiler, "build", "-o", str(out_path), str(source_path)]
        return cls._run_compiler_command(cmd, out_path)

    @classmethod
    def _run_compiler_command(
        cls, cmd: list[str], output_path: Path
    ) -> CompilationResult:
        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError as e:
            raise CompilationError(f"Failed to execute compiler '{cmd[0]}': {e}") from e

        if res.returncode != 0 or not output_path.exists():
            error_details = (res.stderr or res.stdout).strip()
            raise CompilationError(
                f"Compilation failed with exit code {res.returncode}:\n{error_details}",
                stdout=res.stdout,
                stderr=res.stderr,
            )

        return CompilationResult(
            success=True,
            executable_path=output_path,
            cached=False,
            stdout=res.stdout,
            stderr=res.stderr,
        )
