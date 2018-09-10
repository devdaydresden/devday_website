'use strict';

var gulp   = require('gulp');
var config = require('../../config');

gulp.task('copy-assets', function(callback) {
    return gulp.src(config.docs.assets.src)
        .pipe(gulp.dest(config.docs.assets.dest));
});