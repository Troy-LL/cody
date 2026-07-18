# Language mode case-fold

`speak` case-folds `language_mode`. Accepted values after fold: `en`, `tl`, `taglish`. `auto` and any other value soft-fail as `false` — orchestration resolves `auto` before calling `speak`.
