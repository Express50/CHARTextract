process.env.PATH = process.env.VIRTUAL_ENV + ";" + process.env.PATH;

let path = require('path');
let python_shell = require('python-shell');
let path_helper = require("../path_helper/paths");
let scriptPath = null;
const isDev = require('electron-is-dev');

if (isDev) {
	console.log('Running in development');
	scriptPath = path.resolve(__dirname, "..", "..", "RegexNLP-py", "__main_simple__.py");
	console.log("App Root: " + path_helper.getAppRoot());
} else {
    python_shell.defaultOptions = { pythonPath: path.resolve(__dirname, "..", "RegexNLP-py", "RegexNLP.exe")};
    scriptPath = "";
}

let pyshell = new python_shell(scriptPath,
        { mode: 'json' },
        function (err, results){ console.log(results); });

pyshell.on('message', function(message) {
    if (message['debug'] !== undefined) {
        console.log(message['debug']);
    } else if (message['app_ready'] !== undefined) {
        console.log("Python application ready");
        pyshell.send({'function': 'set_cwd', 'params': {'current_dir': path_helper.getAppRoot()}});
    } else {
        pyshell.emit("response", message);
    }
});

module.exports = pyshell;