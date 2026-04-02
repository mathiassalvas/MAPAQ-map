# Deploy notes — GitHub Pages

- This repository is published to GitHub Pages by a GitHub Actions workflow.
- The workflow publishes the `MAPAQ-map` folder (contents) as the Pages site artifact.

How it works
- Pushes to the `main` branch trigger `.github/workflows/gh-pages.yml`.
- The action uploads the `MAPAQ-map` folder and deploys it via the Pages deploy action.

If you want to publish a different folder
- Edit `.github/workflows/gh-pages.yml` and change the `path` under `upload-pages-artifact`.

Manual redeploy
- Re-run the workflow from the Actions tab in GitHub or push an empty commit:

```bash
git commit --allow-empty -m "trigger pages redeploy" && git push
```
