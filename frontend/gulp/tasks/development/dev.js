var browserSync = require('browser-sync');
var reload      = browserSync.reload;
var gulp        = require('gulp');
var config      = require('../../config');


function dev(cb) {
    gulp.series(browser_sync, function() {
        gulp.watch( config.html.src, html_bs);
        gulp.watch( config.sass.allsrc, sass_bs);
        gulp.watch( config.js.src, js_bs);
    });
}

function browser_sync(cb) {
    browserSync({
        server: config.basepath,
        logConnections: true,
        logFileChanges: true
    });
    cb();
}

function bs_reload(cb) {
    browserSync.reload();
    cb();
}
