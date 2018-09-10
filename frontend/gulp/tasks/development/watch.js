var gulp   = require('gulp');
var config = require('../../config');

// Watch Files For Changes
gulp.task('watch', function() {
    gulp.watch(config.js.src, ['js']);
    gulp.watch(config.sass.allsrc, ['sass']);
});