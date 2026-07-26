# Example project

## Quick start

```sh
mkdir -p .firstrun-example
printf 'ready\n' > .firstrun-example/status
```

```sh
test "$(cat .firstrun-example/status)" = ready
rm -rf .firstrun-example
```

```powershell
New-Item -ItemType Directory -Force .firstrun-example | Out-Null
Set-Content .firstrun-example/status ready
```

```powershell
if ((Get-Content .firstrun-example/status) -ne 'ready') { exit 1 }
Remove-Item .firstrun-example -Recurse -Force
```

