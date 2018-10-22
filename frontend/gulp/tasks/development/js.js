var gulp       = require('gulp');
var sourcemaps = require('gulp-sourcemaps');
var concat     = require('gulp-concat');
var uglify     = require('gulp-uglify');
var gulpif     = require('gulp-if');
var plumber    = require('gulp-plumber');
var minimist   = require('minimist');
var header     = require('gulp-header');
var fs         = require('fs');
var config     = require('../../config');


var options      = minimist(process.argv.slice(2), config.environment);

// concat javascript files
// write sourcemaps and uglify if param production is set
gulp.task('js', function(callback) {
    var result = gulp.src(config.js.src)
        .pipe(gulpif(options.env === config.environment.production, sourcemaps.init({
            loadMaps: true
        }))) // init source maps in production
        //.pipe(plumber())
        //.pipe(header(config.strings.banner))
        .pipe(concat(config.js.filename))
        .pipe(gulpif(options.env === config.environment.production, uglify())) // only minify in production
        .pipe(gulpif(options.env === config.environment.production, sourcemaps.write('.'))) //write sourcemap in production
        .pipe(gulp.dest(config.js.dest));

    if (fs.existsSync(config.js.dest + "/" + config.js.filename) && !fs.existsSync(config.js.dest + "/" + config.js.minFilename)) {
        fs.createReadStream(config.js.dest + "/" + config.js.filename)
            .pipe(fs.createWriteStream(config.js.dest + "/" + config.js.minFilename));
    }
    if (!fs.existsSync(config.js.dest + "/" + config.js.filename) && fs.existsSync(config.js.dest + "/" + config.js.minFilename)) {
        fs.createReadStream(config.js.dest + "/" + config.js.minFilename)
            .pipe(fs.createWriteStream(config.js.dest + "/" + config.js.filename));
    }

    return result;
});

gulp.task('js-bs', function(callback) {
    return gulp.src(config.js.src)
        .pipe(gulpif(options.env === config.environment.production, sourcemaps.init({
            loadMaps: true
        }))) // init source maps in production
        .pipe(plumber())
        .pipe(header(config.strings.banner))
        .pipe(concat(config.js.filename))
        .pipe(gulpif(options.env === config.environment.production, uglify())) // only minify in production
        .pipe(gulpif(options.env === config.environment.production, sourcemaps.write('.'))) //write sourcemap in production
        .pipe(gulp.dest(config.js.dest)
        .on('end', function() {
             gulp.start(['bs-reload']);
        }));
});
