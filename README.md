# krooster-stats

## Getting Krooster data

Navigate to [Krooster.com](https://www.krooster.com/) and copy the local storage value corresponding to `"operators"` into a JSON file.

**Optional (but recommended):** get a lot of friends to do the same. Save all `.json` files in the same directory.

On Chromium browsers: open DevTools (F12) and navigate to `Application > Local Storage > https://www.krooster.com`.

## Running the script

Run the script while specifying a directory containing JSON files. For example:

```
python run.py sample_data
```

Results will be saved in the `output/` directory.
