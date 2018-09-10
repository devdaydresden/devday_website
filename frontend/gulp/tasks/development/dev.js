var browserSync = require('browser-sync');
var reload      = browserSync.reload;
var gulp        = require('gulp');
var config      = require('../../config');


gulp.task('dev', ['browser-sync'], function() {

    gulp.watch( config.html.src, ['html-bs']);
    gulp.watch( config.sass.allsrc, [ 'sass-bs' ] );
    gulp.watch( config.js.src, [ 'js-bs'] );

});

gulp.task('browser-sync', function() {
    browserSync({
        server: config.basepath,
        logConnections: true,
        logFileChanges: true
    });
});

gulp.task('bs-reload', function () {
    browserSync.reload();
});
