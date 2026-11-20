/* @preserve
* @terraformer/wkt - v2.2.0 - MIT
* Copyright (c) 2012-2024 Environmental Systems Research Institute, Inc.
* Wed May 15 2024 14:35:51 GMT-0700 (Pacific Daylight Time)
*/
(function (global, factory) {
    typeof exports === 'object' && typeof module !== 'undefined' ? factory(exports) :
    typeof define === 'function' && define.amd ? define(['exports'], factory) :
    (global = typeof globalThis !== 'undefined' ? globalThis : global || self, factory(global.Terraformer = global.Terraformer || {}));
  })(this, (function (exports) { 'use strict';

    /* global parser */ // via jison

    /* Copyright (c) 2012-2020 Environmental Systems Research Institute, Inc.
     * MIT */

    /** @module Terraformer */

    var o = function o(k, v, _o, l) {
        for (_o = _o || {}, l = k.length; l--; _o[k[l]] = v);
        return _o;
      },
      $V0 = [1, 9],
      $V1 = [1, 10],
      $V2 = [1, 11],
      $V3 = [1, 12],
      $V4 = [1, 13],
      $V5 = [1, 14],
      $V6 = [1, 15],
      $V7 = [1, 60],
      $V8 = [5, 15, 19],
      $V9 = [1, 67],
      $Va = [1, 73],
      $Vb = [1, 87],
      $Vc = [1, 104],
      $Vd = [15, 19],
      $Ve = [1, 110],
      $Vf = [1, 116],
      $Vg = [1, 130],
      $Vh = [1, 136];
    var parser = {
      trace: function trace() {},
      yy: {},
      symbols_: {
        "error": 2,
        "expressions": 3,
        "point": 4,
        "EOF": 5,
        "linestring": 6,
        "polygon": 7,
        "multipoint": 8,
        "multilinestring": 9,
        "multipolygon": 10,
        "geometrycollection": 11,
        "coordinate": 12,
        "DOUBLE_TOK": 13,
        "ptarray": 14,
        "COMMA": 15,
        "ring_list": 16,
        "ring": 17,
        "(": 18,
        ")": 19,
        "POINT": 20,
        "Z": 21,
        "ZM": 22,
        "M": 23,
        "EMPTY": 24,
        "point_untagged": 25,
        "polygon_list": 26,
        "polygon_untagged": 27,
        "point_list": 28,
        "LINESTRING": 29,
        "POLYGON": 30,
        "MULTIPOINT": 31,
        "MULTILINESTRING": 32,
        "MULTIPOLYGON": 33,
        "geometry": 34,
        "geometry_collection": 35,
        "GEOMETRYCOLLECTION": 36,
        "$accept": 0,
        "$end": 1
      },
      terminals_: {
        2: "error",
        5: "EOF",
        13: "DOUBLE_TOK",
        15: "COMMA",
        18: "(",
        19: ")",
        20: "POINT",
        21: "Z",
        22: "ZM",
        23: "M",
        24: "EMPTY",
        29: "LINESTRING",
        30: "POLYGON",
        31: "MULTIPOINT",
        32: "MULTILINESTRING",
        33: "MULTIPOLYGON",
        36: "GEOMETRYCOLLECTION"
      },
      productions_: [0, [3, 2], [3, 2], [3, 2], [3, 2], [3, 2], [3, 2], [3, 2], [12, 2], [12, 3], [12, 4], [14, 3], [14, 1], [16, 3], [16, 1], [17, 3], [4, 4], [4, 5], [4, 5], [4, 5], [4, 2], [25, 1], [25, 3], [26, 3], [26, 1], [27, 3], [28, 3], [28, 1], [6, 4], [6, 5], [6, 5], [6, 5], [6, 2], [7, 4], [7, 5], [7, 5], [7, 5], [7, 2], [8, 4], [8, 5], [8, 5], [8, 5], [8, 2], [9, 4], [9, 5], [9, 5], [9, 5], [9, 2], [10, 4], [10, 5], [10, 5], [10, 5], [10, 2], [34, 1], [34, 1], [34, 1], [34, 1], [34, 1], [34, 1], [34, 1], [35, 3], [35, 1], [11, 4], [11, 5], [11, 5], [11, 5], [11, 2]],
      performAction: function anonymous(yytext, yyleng, yylineno, yy, yystate /* action[1] */, $ /* vstack */, _$ /* lstack */) {
        /* this == yyval */

        var $0 = $.length - 1;
        switch (yystate) {
          case 1:
          case 2:
          case 3:
          case 4:
          case 5:
          case 6:
          case 7:
            return $[$0 - 1];
          case 8:
            this.$ = new PointArray([Number($[$0 - 1]), Number($[$0])]);
            break;
          case 9:
            this.$ = new PointArray([Number($[$0 - 2]), Number($[$0 - 1]), Number($[$0])]);
            break;
          case 10:
            this.$ = new PointArray([Number($[$0 - 3]), Number($[$0 - 2]), Number($[$0 - 1]), Number($[$0])]);
            break;
          case 11:
          case 26:
            this.$ = $[$0 - 2].addPoint($[$0]);
            break;
          case 12:
          case 21:
          case 27:
          case 53:
          case 54:
          case 55:
          case 56:
          case 57:
          case 58:
          case 59:
            this.$ = $[$0];
            break;
          case 13:
            this.$ = $[$0 - 2].addRing($[$0]);
            break;
          case 14:
            this.$ = new RingList($[$0]);
            break;
          case 15:
            this.$ = new Ring($[$0 - 1]);
            break;
          case 16:
            this.$ = {
              "type": "Point",
              "coordinates": $[$0 - 1].data[0]
            };
            break;
          case 17:
            this.$ = {
              "type": "Point",
              "coordinates": $[$0 - 1].data[0],
              "properties": {
                z: true
              }
            };
            break;
          case 18:
            this.$ = {
              "type": "Point",
              "coordinates": $[$0 - 1].data[0],
              "properties": {
                z: true,
                m: true
              }
            };
            break;
          case 19:
            this.$ = {
              "type": "Point",
              "coordinates": $[$0 - 1].data[0],
              "properties": {
                m: true
              }
            };
            break;
          case 20:
            this.$ = {
              "type": "Point",
              "coordinates": []
            };
            break;
          case 22:
          case 25:
            this.$ = $[$0 - 1];
            break;
          case 23:
            this.$ = $[$0 - 2].addPolygon($[$0]);
            break;
          case 24:
            this.$ = new PolygonList($[$0]);
            break;
          case 28:
            this.$ = {
              "type": "LineString",
              "coordinates": $[$0 - 1].data
            };
            break;
          case 29:
            this.$ = {
              "type": "LineString",
              "coordinates": $[$0 - 1].data,
              "properties": {
                z: true
              }
            };
            break;
          case 30:
            this.$ = {
              "type": "LineString",
              "coordinates": $[$0 - 1].data,
              "properties": {
                m: true
              }
            };
            break;
          case 31:
            this.$ = {
              "type": "LineString",
              "coordinates": $[$0 - 1].data,
              "properties": {
                z: true,
                m: true
              }
            };
            break;
          case 32:
            this.$ = {
              "type": "LineString",
              "coordinates": []
            };
            break;
          case 33:
            this.$ = {
              "type": "Polygon",
              "coordinates": $[$0 - 1].toJSON()
            };
            break;
          case 34:
            this.$ = {
              "type": "Polygon",
              "coordinates": $[$0 - 1].toJSON(),
              "properties": {
                z: true
              }
            };
            break;
          case 35:
            this.$ = {
              "type": "Polygon",
              "coordinates": $[$0 - 1].toJSON(),
              "properties": {
                m: true
              }
            };
            break;
          case 36:
            this.$ = {
              "type": "Polygon",
              "coordinates": $[$0 - 1].toJSON(),
              "properties": {
                z: true,
                m: true
              }
            };
            break;
          case 37:
            this.$ = {
              "type": "Polygon",
              "coordinates": []
            };
            break;
          case 38:
            this.$ = {
              "type": "MultiPoint",
              "coordinates": $[$0 - 1].data
            };
            break;
          case 39:
            this.$ = {
              "type": "MultiPoint",
              "coordinates": $[$0 - 1].data,
              "properties": {
                z: true
              }
            };
            break;
          case 40:
            this.$ = {
              "type": "MultiPoint",
              "coordinates": $[$0 - 1].data,
              "properties": {
                m: true
              }
            };
            break;
          case 41:
            this.$ = {
              "type": "MultiPoint",
              "coordinates": $[$0 - 1].data,
              "properties": {
                z: true,
                m: true
              }
            };
            break;
          case 42:
            this.$ = {
              "type": "MultiPoint",
              "coordinates": []
            };
            break;
          case 43:
            this.$ = {
              "type": "MultiLineString",
              "coordinates": $[$0 - 1].toJSON()
            };
            break;
          case 44:
            this.$ = {
              "type": "MultiLineString",
              "coordinates": $[$0 - 1].toJSON(),
              "properties": {
                z: true
              }
            };
            break;
          case 45:
            this.$ = {
              "type": "MultiLineString",
              "coordinates": $[$0 - 1].toJSON(),
              "properties": {
                m: true
              }
            };
            break;
          case 46:
            this.$ = {
              "type": "MultiLineString",
              "coordinates": $[$0 - 1].toJSON(),
              "properties": {
                z: true,
                m: true
              }
            };
            break;
          case 47:
            this.$ = {
              "type": "MultiLineString",
              "coordinates": []
            };
            break;
          case 48:
            this.$ = {
              "type": "MultiPolygon",
              "coordinates": $[$0 - 1].toJSON()
            };
            break;
          case 49:
            this.$ = {
              "type": "MultiPolygon",
              "coordinates": $[$0 - 1].toJSON(),
              "properties": {
                z: true
              }
            };
            break;
          case 50:
            this.$ = {
              "type": "MultiPolygon",
              "coordinates": $[$0 - 1].toJSON(),
              "properties": {
                m: true
              }
            };
            break;
          case 51:
            this.$ = {
              "type": "MultiPolygon",
              "coordinates": $[$0 - 1].toJSON(),
              "properties": {
                z: true,
                m: true
              }
            };
            break;
          case 52:
            this.$ = {
              "type": "MultiPolygon",
              "coordinates": []
            };
            break;
          case 60:
            this.$ = $[$0 - 2].addGeometry($[$0]);
            break;
          case 61:
            this.$ = new GeometryList($[$0]);
            break;
          case 62:
            this.$ = {
              "type": "GeometryCollection",
              "geometries": $[$0 - 1].toJSON()
            };
            break;
          case 63:
            this.$ = {
              "type": "GeometryCollection",
              "geometries": $[$0 - 1].toJSON(),
              "properties": {
                z: true
              }
            };
            break;
          case 64:
            this.$ = {
              "type": "GeometryCollection",
              "geometries": $[$0 - 1].toJSON(),
              "properties": {
                m: true
              }
            };
            break;
          case 65:
            this.$ = {
              "type": "GeometryCollection",
              "geometries": $[$0 - 1].toJSON(),
              "properties": {
                z: true,
                m: true
              }
            };
            break;
          case 66:
            this.$ = {
              "type": "GeometryCollection",
              "geometries": []
            };
            break;
        }
      },
      table: [{
        3: 1,
        4: 2,
        6: 3,
        7: 4,
        8: 5,
        9: 6,
        10: 7,
        11: 8,
        20: $V0,
        29: $V1,
        30: $V2,
        31: $V3,
        32: $V4,
        33: $V5,
        36: $V6
      }, {
        1: [3]
      }, {
        5: [1, 16]
      }, {
        5: [1, 17]
      }, {
        5: [1, 18]
      }, {
        5: [1, 19]
      }, {
        5: [1, 20]
      }, {
        5: [1, 21]
      }, {
        5: [1, 22]
      }, {
        18: [1, 23],
        21: [1, 24],
        22: [1, 25],
        23: [1, 26],
        24: [1, 27]
      }, {
        18: [1, 28],
        21: [1, 29],
        22: [1, 31],
        23: [1, 30],
        24: [1, 32]
      }, {
        18: [1, 33],
        21: [1, 34],
        22: [1, 36],
        23: [1, 35],
        24: [1, 37]
      }, {
        18: [1, 38],
        21: [1, 39],
        22: [1, 41],
        23: [1, 40],
        24: [1, 42]
      }, {
        18: [1, 43],
        21: [1, 44],
        22: [1, 46],
        23: [1, 45],
        24: [1, 47]
      }, {
        18: [1, 48],
        21: [1, 49],
        22: [1, 51],
        23: [1, 50],
        24: [1, 52]
      }, {
        18: [1, 53],
        21: [1, 54],
        22: [1, 56],
        23: [1, 55],
        24: [1, 57]
      }, {
        1: [2, 1]
      }, {
        1: [2, 2]
      }, {
        1: [2, 3]
      }, {
        1: [2, 4]
      }, {
        1: [2, 5]
      }, {
        1: [2, 6]
      }, {
        1: [2, 7]
      }, {
        12: 59,
        13: $V7,
        14: 58
      }, {
        18: [1, 61]
      }, {
        18: [1, 62]
      }, {
        18: [1, 63]
      }, o($V8, [2, 20]), {
        12: 66,
        13: $V7,
        18: $V9,
        25: 65,
        28: 64
      }, {
        18: [1, 68]
      }, {
        18: [1, 69]
      }, {
        18: [1, 70]
      }, o($V8, [2, 32]), {
        16: 71,
        17: 72,
        18: $Va
      }, {
        18: [1, 74]
      }, {
        18: [1, 75]
      }, {
        18: [1, 76]
      }, o($V8, [2, 37]), {
        12: 66,
        13: $V7,
        18: $V9,
        25: 65,
        28: 77
      }, {
        18: [1, 78]
      }, {
        18: [1, 79]
      }, {
        18: [1, 80]
      }, o($V8, [2, 42]), {
        16: 81,
        17: 72,
        18: $Va
      }, {
        18: [1, 82]
      }, {
        18: [1, 83]
      }, {
        18: [1, 84]
      }, o($V8, [2, 47]), {
        18: $Vb,
        26: 85,
        27: 86
      }, {
        18: [1, 88]
      }, {
        18: [1, 89]
      }, {
        18: [1, 90]
      }, o($V8, [2, 52]), {
        4: 93,
        6: 94,
        7: 95,
        8: 96,
        9: 97,
        10: 98,
        11: 99,
        20: $V0,
        29: $V1,
        30: $V2,
        31: $V3,
        32: $V4,
        33: $V5,
        34: 92,
        35: 91,
        36: $V6
      }, {
        18: [1, 100]
      }, {
        18: [1, 101]
      }, {
        18: [1, 102]
      }, o($V8, [2, 66]), {
        15: $Vc,
        19: [1, 103]
      }, o($Vd, [2, 12]), {
        13: [1, 105]
      }, {
        12: 59,
        13: $V7,
        14: 106
      }, {
        12: 59,
        13: $V7,
        14: 107
      }, {
        12: 59,
        13: $V7,
        14: 108
      }, {
        15: $Ve,
        19: [1, 109]
      }, o($Vd, [2, 27]), o($Vd, [2, 21]), {
        12: 111,
        13: $V7
      }, {
        12: 66,
        13: $V7,
        18: $V9,
        25: 65,
        28: 112
      }, {
        12: 66,
        13: $V7,
        18: $V9,
        25: 65,
        28: 113
      }, {
        12: 66,
        13: $V7,
        18: $V9,
        25: 65,
        28: 114
      }, {
        15: $Vf,
        19: [1, 115]
      }, o($Vd, [2, 14]), {
        12: 59,
        13: $V7,
        14: 117
      }, {
        16: 118,
        17: 72,
        18: $Va
      }, {
        16: 119,
        17: 72,
        18: $Va
      }, {
        16: 120,
        17: 72,
        18: $Va
      }, {
        15: $Ve,
        19: [1, 121]
      }, {
        12: 66,
        13: $V7,
        18: $V9,
        25: 65,
        28: 122
      }, {
        12: 66,
        13: $V7,
        18: $V9,
        25: 65,
        28: 123
      }, {
        12: 66,
        13: $V7,
        18: $V9,
        25: 65,
        28: 124
      }, {
        15: $Vf,
        19: [1, 125]
      }, {
        16: 126,
        17: 72,
        18: $Va
      }, {
        16: 127,
        17: 72,
        18: $Va
      }, {
        16: 128,
        17: 72,
        18: $Va
      }, {
        15: $Vg,
        19: [1, 129]
      }, o($Vd, [2, 24]), {
        16: 131,
        17: 72,
        18: $Va
      }, {
        18: $Vb,
        26: 132,
        27: 86
      }, {
        18: $Vb,
        26: 133,
        27: 86
      }, {
        18: $Vb,
        26: 134,
        27: 86
      }, {
        15: $Vh,
        19: [1, 135]
      }, o($Vd, [2, 61]), o($Vd, [2, 53]), o($Vd, [2, 54]), o($Vd, [2, 55]), o($Vd, [2, 56]), o($Vd, [2, 57]), o($Vd, [2, 58]), o($Vd, [2, 59]), {
        4: 93,
        6: 94,
        7: 95,
        8: 96,
        9: 97,
        10: 98,
        11: 99,
        20: $V0,
        29: $V1,
        30: $V2,
        31: $V3,
        32: $V4,
        33: $V5,
        34: 92,
        35: 137,
        36: $V6
      }, {
        4: 93,
        6: 94,
        7: 95,
        8: 96,
        9: 97,
        10: 98,
        11: 99,
        20: $V0,
        29: $V1,
        30: $V2,
        31: $V3,
        32: $V4,
        33: $V5,
        34: 92,
        35: 138,
        36: $V6
      }, {
        4: 93,
        6: 94,
        7: 95,
        8: 96,
        9: 97,
        10: 98,
        11: 99,
        20: $V0,
        29: $V1,
        30: $V2,
        31: $V3,
        32: $V4,
        33: $V5,
        34: 92,
        35: 139,
        36: $V6
      }, o($V8, [2, 16]), {
        12: 140,
        13: $V7
      }, o($Vd, [2, 8], {
        13: [1, 141]
      }), {
        15: $Vc,
        19: [1, 142]
      }, {
        15: $Vc,
        19: [1, 143]
      }, {
        15: $Vc,
        19: [1, 144]
      }, o($V8, [2, 28]), {
        12: 66,
        13: $V7,
        18: $V9,
        25: 145
      }, {
        19: [1, 146]
      }, {
        15: $Ve,
        19: [1, 147]
      }, {
        15: $Ve,
        19: [1, 148]
      }, {
        15: $Ve,
        19: [1, 149]
      }, o($V8, [2, 33]), {
        17: 150,
        18: $Va
      }, {
        15: $Vc,
        19: [1, 151]
      }, {
        15: $Vf,
        19: [1, 152]
      }, {
        15: $Vf,
        19: [1, 153]
      }, {
        15: $Vf,
        19: [1, 154]
      }, o($V8, [2, 38]), {
        15: $Ve,
        19: [1, 155]
      }, {
        15: $Ve,
        19: [1, 156]
      }, {
        15: $Ve,
        19: [1, 157]
      }, o($V8, [2, 43]), {
        15: $Vf,
        19: [1, 158]
      }, {
        15: $Vf,
        19: [1, 159]
      }, {
        15: $Vf,
        19: [1, 160]
      }, o($V8, [2, 48]), {
        18: $Vb,
        27: 161
      }, {
        15: $Vf,
        19: [1, 162]
      }, {
        15: $Vg,
        19: [1, 163]
      }, {
        15: $Vg,
        19: [1, 164]
      }, {
        15: $Vg,
        19: [1, 165]
      }, o($V8, [2, 62]), {
        4: 93,
        6: 94,
        7: 95,
        8: 96,
        9: 97,
        10: 98,
        11: 99,
        20: $V0,
        29: $V1,
        30: $V2,
        31: $V3,
        32: $V4,
        33: $V5,
        34: 166,
        36: $V6
      }, {
        15: $Vh,
        19: [1, 167]
      }, {
        15: $Vh,
        19: [1, 168]
      }, {
        15: $Vh,
        19: [1, 169]
      }, o($Vd, [2, 11]), o($Vd, [2, 9], {
        13: [1, 170]
      }), o($V8, [2, 17]), o($V8, [2, 18]), o($V8, [2, 19]), o($Vd, [2, 26]), o($Vd, [2, 22]), o($V8, [2, 29]), o($V8, [2, 30]), o($V8, [2, 31]), o($Vd, [2, 13]), o($Vd, [2, 15]), o($V8, [2, 34]), o($V8, [2, 35]), o($V8, [2, 36]), o($V8, [2, 39]), o($V8, [2, 40]), o($V8, [2, 41]), o($V8, [2, 44]), o($V8, [2, 45]), o($V8, [2, 46]), o($Vd, [2, 23]), o($Vd, [2, 25]), o($V8, [2, 49]), o($V8, [2, 50]), o($V8, [2, 51]), o($Vd, [2, 60]), o($V8, [2, 63]), o($V8, [2, 64]), o($V8, [2, 65]), o($Vd, [2, 10])],
      defaultActions: {
        16: [2, 1],
        17: [2, 2],
        18: [2, 3],
        19: [2, 4],
        20: [2, 5],
        21: [2, 6],
        22: [2, 7]
      },
      parseError: function parseError(str, hash) {
        if (hash.recoverable) {
          this.trace(str);
        } else {
          var error = new Error(str);
          error.hash = hash;
          throw error;
        }
      },
      parse: function parse(input) {
        var self = this,
          stack = [0],
          vstack = [null],
          lstack = [],
          table = this.table,
          yytext = '',
          yylineno = 0,
          yyleng = 0,
          TERROR = 2,
          EOF = 1;
        var args = lstack.slice.call(arguments, 1);
        var lexer = Object.create(this.lexer);
        var sharedState = {
          yy: {}
        };
        for (var k in this.yy) {
          if (Object.prototype.hasOwnProperty.call(this.yy, k)) {
            sharedState.yy[k] = this.yy[k];
          }
        }
        lexer.setInput(input, sharedState.yy);
        sharedState.yy.lexer = lexer;
        sharedState.yy.parser = this;
        if (typeof lexer.yylloc == 'undefined') {
          lexer.yylloc = {};
        }
        var yyloc = lexer.yylloc;
        lstack.push(yyloc);
        var ranges = lexer.options && lexer.options.ranges;
        if (typeof sharedState.yy.parseError === 'function') {
          this.parseError = sharedState.yy.parseError;
        } else {
          this.parseError = Object.getPrototypeOf(this).parseError;
        }
        var lex = function lex() {
          var token;
          token = lexer.lex() || EOF;
          if (typeof token !== 'number') {
            token = self.symbols_[token] || token;
          }
          return token;
        };
        var symbol,
          state,
          action,
          r,
          yyval = {},
          p,
          len,
          newState,
          expected;
        while (true) {
          state = stack[stack.length - 1];
          if (this.defaultActions[state]) {
            action = this.defaultActions[state];
          } else {
            if (symbol === null || typeof symbol == 'undefined') {
              symbol = lex();
            }
            action = table[state] && table[state][symbol];
          }
          if (typeof action === 'undefined' || !action.length || !action[0]) {
            var errStr = '';
            expected = [];
            for (p in table[state]) {
              if (this.terminals_[p] && p > TERROR) {
                expected.push('\'' + this.terminals_[p] + '\'');
              }
            }
            if (lexer.showPosition) {
              errStr = 'Parse error on line ' + (yylineno + 1) + ':\n' + lexer.showPosition() + '\nExpecting ' + expected.join(', ') + ', got \'' + (this.terminals_[symbol] || symbol) + '\'';
            } else {
              errStr = 'Parse error on line ' + (yylineno + 1) + ': Unexpected ' + (symbol == EOF ? 'end of input' : '\'' + (this.terminals_[symbol] || symbol) + '\'');
            }
            this.parseError(errStr, {
              text: lexer.match,
              token: this.terminals_[symbol] || symbol,
              line: lexer.yylineno,
              loc: yyloc,
              expected: expected
            });
          }
          if (action[0] instanceof Array && action.length > 1) {
            throw new Error('Parse Error: multiple actions possible at state: ' + state + ', token: ' + symbol);
          }
          switch (action[0]) {
            case 1:
              stack.push(symbol);
              vstack.push(lexer.yytext);
              lstack.push(lexer.yylloc);
              stack.push(action[1]);
              symbol = null;
              {
                yyleng = lexer.yyleng;
                yytext = lexer.yytext;
                yylineno = lexer.yylineno;
                yyloc = lexer.yylloc;
              }
              break;
            case 2:
              len = this.productions_[action[1]][1];
              yyval.$ = vstack[vstack.length - len];
              yyval._$ = {
                first_line: lstack[lstack.length - (len || 1)].first_line,
                last_line: lstack[lstack.length - 1].last_line,
                first_column: lstack[lstack.length - (len || 1)].first_column,
                last_column: lstack[lstack.length - 1].last_column
              };
              if (ranges) {
                yyval._$.range = [lstack[lstack.length - (len || 1)].range[0], lstack[lstack.length - 1].range[1]];
              }
              r = this.performAction.apply(yyval, [yytext, yyleng, yylineno, sharedState.yy, action[1], vstack, lstack].concat(args));
              if (typeof r !== 'undefined') {
                return r;
              }
              if (len) {
                stack = stack.slice(0, -1 * len * 2);
                vstack = vstack.slice(0, -1 * len);
                lstack = lstack.slice(0, -1 * len);
              }
              stack.push(this.productions_[action[1]][0]);
              vstack.push(yyval.$);
              lstack.push(yyval._$);
              newState = table[stack[stack.length - 2]][stack[stack.length - 1]];
              stack.push(newState);
              break;
            case 3:
              return true;
          }
        }
        return true;
      }
    };

    /* generated by jison-lex 0.3.4 */
    var lexer = function () {
      var lexer = {
        EOF: 1,
        parseError: function parseError(str, hash) {
          if (this.yy.parser) {
            this.yy.parser.parseError(str, hash);
          } else {
            throw new Error(str);
          }
        },
        // resets the lexer, sets new input
        setInput: function setInput(input, yy) {
          this.yy = yy || this.yy || {};
          this._input = input;
          this._more = this._backtrack = this.done = false;
          this.yylineno = this.yyleng = 0;
          this.yytext = this.matched = this.match = '';
          this.conditionStack = ['INITIAL'];
          this.yylloc = {
            first_line: 1,
            first_column: 0,
            last_line: 1,
            last_column: 0
          };
          if (this.options.ranges) {
            this.yylloc.range = [0, 0];
          }
          this.offset = 0;
          return this;
        },
        // consumes and returns one char from the input
        input: function input() {
          var ch = this._input[0];
          this.yytext += ch;
          this.yyleng++;
          this.offset++;
          this.match += ch;
          this.matched += ch;
          var lines = ch.match(/(?:\r\n?|\n).*/g);
          if (lines) {
            this.yylineno++;
            this.yylloc.last_line++;
          } else {
            this.yylloc.last_column++;
          }
          if (this.options.ranges) {
            this.yylloc.range[1]++;
          }
          this._input = this._input.slice(1);
          return ch;
        },
        // unshifts one char (or a string) into the input
        unput: function unput(ch) {
          var len = ch.length;
          var lines = ch.split(/(?:\r\n?|\n)/g);
          this._input = ch + this._input;
          this.yytext = this.yytext.substr(0, this.yytext.length - len);
          //this.yyleng -= len;
          this.offset -= len;
          var oldLines = this.match.split(/(?:\r\n?|\n)/g);
          this.match = this.match.substr(0, this.match.length - 1);
          this.matched = this.matched.substr(0, this.matched.length - 1);
          if (lines.length - 1) {
            this.yylineno -= lines.length - 1;
          }
          var r = this.yylloc.range;
          this.yylloc = {
            first_line: this.yylloc.first_line,
            last_line: this.yylineno + 1,
            first_column: this.yylloc.first_column,
            last_column: lines ? (lines.length === oldLines.length ? this.yylloc.first_column : 0) + oldLines[oldLines.length - lines.length].length - lines[0].length : this.yylloc.first_column - len
          };
          if (this.options.ranges) {
            this.yylloc.range = [r[0], r[0] + this.yyleng - len];
          }
          this.yyleng = this.yytext.length;
          return this;
        },
        // When called from action, caches matched text and appends it on next action
        more: function more() {
          this._more = true;
          return this;
        },
        // When called from action, signals the lexer that this rule fails to match the input, so the next matching rule (regex) should be tested instead.
        reject: function reject() {
          if (this.options.backtrack_lexer) {
            this._backtrack = true;
          } else {
            return this.parseError('Lexical error on line ' + (this.yylineno + 1) + '. You can only invoke reject() in the lexer when the lexer is of the backtracking persuasion (options.backtrack_lexer = true).\n' + this.showPosition(), {
              text: "",
              token: null,
              line: this.yylineno
            });
          }
          return this;
        },
        // retain first n characters of the match
        less: function less(n) {
          this.unput(this.match.slice(n));
        },
        // displays already matched input, i.e. for error messages
        pastInput: function pastInput() {
          var past = this.matched.substr(0, this.matched.length - this.match.length);
          return (past.length > 20 ? '...' : '') + past.substr(-20).replace(/\n/g, "");
        },
        // displays upcoming input, i.e. for error messages
        upcomingInput: function upcomingInput() {
          var next = this.match;
          if (next.length < 20) {
            next += this._input.substr(0, 20 - next.length);
          }
          return (next.substr(0, 20) + (next.length > 20 ? '...' : '')).replace(/\n/g, "");
        },
        // displays the character position where the lexing error occurred, i.e. for error messages
        showPosition: function showPosition() {
          var pre = this.pastInput();
          var c = new Array(pre.length + 1).join("-");
          return pre + this.upcomingInput() + "\n" + c + "^";
        },
        // test the lexed token: return FALSE when not a match, otherwise return token
        test_match: function test_match(match, indexed_rule) {
          var token, lines, backup;
          if (this.options.backtrack_lexer) {
            // save context
            backup = {
              yylineno: this.yylineno,
              yylloc: {
                first_line: this.yylloc.first_line,
                last_line: this.last_line,
                first_column: this.yylloc.first_column,
                last_column: this.yylloc.last_column
              },
              yytext: this.yytext,
              match: this.match,
              matches: this.matches,
              matched: this.matched,
              yyleng: this.yyleng,
              offset: this.offset,
              _more: this._more,
              _input: this._input,
              yy: this.yy,
              conditionStack: this.conditionStack.slice(0),
              done: this.done
            };
            if (this.options.ranges) {
              backup.yylloc.range = this.yylloc.range.slice(0);
            }
          }
          lines = match[0].match(/(?:\r\n?|\n).*/g);
          if (lines) {
            this.yylineno += lines.length;
          }
          this.yylloc = {
            first_line: this.yylloc.last_line,
            last_line: this.yylineno + 1,
            first_column: this.yylloc.last_column,
            last_column: lines ? lines[lines.length - 1].length - lines[lines.length - 1].match(/\r?\n?/)[0].length : this.yylloc.last_column + match[0].length
          };
          this.yytext += match[0];
          this.match += match[0];
          this.matches = match;
          this.yyleng = this.yytext.length;
          if (this.options.ranges) {
            this.yylloc.range = [this.offset, this.offset += this.yyleng];
          }
          this._more = false;
          this._backtrack = false;
          this._input = this._input.slice(match[0].length);
          this.matched += match[0];
          token = this.performAction.call(this, this.yy, this, indexed_rule, this.conditionStack[this.conditionStack.length - 1]);
          if (this.done && this._input) {
            this.done = false;
          }
          if (token) {
            return token;
          } else if (this._backtrack) {
            // recover context
            for (var k in backup) {
              this[k] = backup[k];
            }
            return false; // rule action called reject() implying the next rule should be tested instead.
          }
          return false;
        },
        // return next match in input
        next: function next() {
          if (this.done) {
            return this.EOF;
          }
          if (!this._input) {
            this.done = true;
          }
          var token, match, tempMatch, index;
          if (!this._more) {
            this.yytext = '';
            this.match = '';
          }
          var rules = this._currentRules();
          for (var i = 0; i < rules.length; i++) {
            tempMatch = this._input.match(this.rules[rules[i]]);
            if (tempMatch && (!match || tempMatch[0].length > match[0].length)) {
              match = tempMatch;
              index = i;
              if (this.options.backtrack_lexer) {
                token = this.test_match(tempMatch, rules[i]);
                if (token !== false) {
                  return token;
                } else if (this._backtrack) {
                  match = false;
                  continue; // rule action called reject() implying a rule MISmatch.
                } else {
                  // else: this is a lexer rule which consumes input without producing a token (e.g. whitespace)
                  return false;
                }
              } else if (!this.options.flex) {
                break;
              }
            }
          }
          if (match) {
            token = this.test_match(match, rules[index]);
            if (token !== false) {
              return token;
            }
            // else: this is a lexer rule which consumes input without producing a token (e.g. whitespace)
            return false;
          }
          if (this._input === "") {
            return this.EOF;
          } else {
            return this.parseError('Lexical error on line ' + (this.yylineno + 1) + '. Unrecognized text.\n' + this.showPosition(), {
              text: "",
              token: null,
              line: this.yylineno
            });
          }
        },
        // return next match that has a token
        lex: function lex() {
          var r = this.next();
          if (r) {
            return r;
          } else {
            return this.lex();
          }
        },
        // activates a new lexer condition state (pushes the new lexer condition state onto the condition stack)
        begin: function begin(condition) {
          this.conditionStack.push(condition);
        },
        // pop the previously active lexer condition state off the condition stack
        popState: function popState() {
          var n = this.conditionStack.length - 1;
          if (n > 0) {
            return this.conditionStack.pop();
          } else {
            return this.conditionStack[0];
          }
        },
        // produce the lexer rule set which is active for the currently active lexer condition state
        _currentRules: function _currentRules() {
          if (this.conditionStack.length && this.conditionStack[this.conditionStack.length - 1]) {
            return this.conditions[this.conditionStack[this.conditionStack.length - 1]].rules;
          } else {
            return this.conditions["INITIAL"].rules;
          }
        },
        // return the currently active lexer condition state; when an index argument is provided it produces the N-th previous condition state, if available
        topState: function topState(n) {
          n = this.conditionStack.length - 1 - Math.abs(n || 0);
          if (n >= 0) {
            return this.conditionStack[n];
          } else {
            return "INITIAL";
          }
        },
        // alias for begin(condition)
        pushState: function pushState(condition) {
          this.begin(condition);
        },
        // return the number of states currently on the stack
        stateStackSize: function stateStackSize() {
          return this.conditionStack.length;
        },
        options: {},
        performAction: function anonymous(yy, yy_, $avoiding_name_collisions, YY_START) {
          switch ($avoiding_name_collisions) {
            case 0:
              // ignore
              break;
            case 1:
              return 18;
            case 2:
              return 19;
            case 3:
              return 13;
            case 4:
              return 20;
            case 5:
              return 29;
            case 6:
              return 30;
            case 7:
              return 31;
            case 8:
              return 32;
            case 9:
              return 33;
            case 10:
              return 36;
            case 11:
              return 15;
            case 12:
              return 24;
            case 13:
              return 23;
            case 14:
              return 21;
            case 15:
              return 22;
            case 16:
              return 5;
            case 17:
              return "INVALID";
          }
        },
        rules: [/^(?:\s+)/, /^(?:\()/, /^(?:\))/, /^(?:-?[0-9]+(\.[0-9]+)?([eE][\-\+]?[0-9]+)?)/, /^(?:POINT\b)/, /^(?:LINESTRING\b)/, /^(?:POLYGON\b)/, /^(?:MULTIPOINT\b)/, /^(?:MULTILINESTRING\b)/, /^(?:MULTIPOLYGON\b)/, /^(?:GEOMETRYCOLLECTION\b)/, /^(?:,)/, /^(?:EMPTY\b)/, /^(?:M\b)/, /^(?:Z\b)/, /^(?:ZM\b)/, /^(?:$)/, /^(?:.)/],
        conditions: {
          "INITIAL": {
            "rules": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17],
            "inclusive": true
          }
        }
      };
      return lexer;
    }();
    parser.lexer = lexer;
    function Parser() {
      this.yy = {};
    }
    Parser.prototype = parser;
    parser.Parser = Parser;

    // surface parsing errors to calling code https://github.com/zaach/jison/issues/218
    parser.yy.parseError = function (err) {
      throw err;
    };
    function PointArray(point) {
      this.data = [point];
      this.type = 'PointArray';
    }
    PointArray.prototype.addPoint = function (point) {
      if (point.type === 'PointArray') {
        this.data = this.data.concat(point.data);
      } else {
        this.data.push(point);
      }
      return this;
    };
    PointArray.prototype.toJSON = function () {
      return this.data;
    };
    function Ring(point) {
      this.data = point;
      this.type = 'Ring';
    }
    Ring.prototype.toJSON = function () {
      var data = [];
      for (var i = 0; i < this.data.data.length; i++) {
        data.push(this.data.data[i]);
      }
      return data;
    };
    function RingList(ring) {
      this.data = [ring];
      this.type = 'RingList';
    }
    RingList.prototype.addRing = function (ring) {
      this.data.push(ring);
      return this;
    };
    RingList.prototype.toJSON = function () {
      var data = [];
      for (var i = 0; i < this.data.length; i++) {
        data.push(this.data[i].toJSON());
      }
      if (data.length === 1) {
        return data;
      } else {
        return data;
      }
    };
    function GeometryList(geometry) {
      this.data = [geometry];
      this.type = 'GeometryList';
    }
    GeometryList.prototype.addGeometry = function (geometry) {
      this.data.push(geometry);
      return this;
    };
    GeometryList.prototype.toJSON = function () {
      return this.data;
    };
    function PolygonList(polygon) {
      this.data = [polygon];
      this.type = 'PolygonList';
    }
    PolygonList.prototype.addPolygon = function (polygon) {
      this.data.push(polygon);
      return this;
    };
    PolygonList.prototype.toJSON = function () {
      var data = [];
      for (var i = 0; i < this.data.length; i++) {
        data = data.concat([this.data[i].toJSON()]);
      }
      return data;
    };

    /**
     * Converts a [WKT](https://en.wikipedia.org/wiki/Well-known_text_representation_of_geometry) geometry into a GeoJSON geometry.
     * @function
     * @param {string} WKT - The input WKT geometry.
     * @return {object} GeoJSON.
     *
     * ```js
     * import { wktToGeoJSON } from "@terraformer/wkt"
     *
     * wktToGeoJSON("POINT (-122.6764 45.5165)");
     *
     * >> { "type": "Point", "coordinates": [ -122.6764, 45.5165 ] }
     * ```
     */
    var wktToGeoJSON = function wktToGeoJSON(element) {
      var res;
      try {
        res = parser.parse(element);
      } catch (err) {
        throw Error('Unable to parse: ' + err);
      }
      return res;
    };
    var arrayToRing = function arrayToRing(arr) {
      var parts = [];
      var ret = '';
      for (var i = 0; i < arr.length; i++) {
        parts.push(arr[i].join(' '));
      }
      ret += '(' + parts.join(', ') + ')';
      return ret;
    };
    var pointToWKTPoint = function pointToWKTPoint(geojson) {
      var ret = 'POINT ';
      if (geojson.coordinates === undefined || geojson.coordinates.length === 0) {
        ret += 'EMPTY';
        return ret;
      } else if (geojson.coordinates.length === 3) {
        // 3d or time? default to 3d
        if (geojson.properties && geojson.properties.m === true) {
          ret += 'M ';
        } else {
          ret += 'Z ';
        }
      } else if (geojson.coordinates.length === 4) {
        // 3d and time
        ret += 'ZM ';
      }

      // include coordinates
      ret += '(' + geojson.coordinates.join(' ') + ')';
      return ret;
    };
    var lineStringToWKTLineString = function lineStringToWKTLineString(geojson) {
      var ret = 'LINESTRING ';
      if (geojson.coordinates === undefined || geojson.coordinates.length === 0 || geojson.coordinates[0].length === 0) {
        ret += 'EMPTY';
        return ret;
      } else if (geojson.coordinates[0].length === 3) {
        if (geojson.properties && geojson.properties.m === true) {
          ret += 'M ';
        } else {
          ret += 'Z ';
        }
      } else if (geojson.coordinates[0].length === 4) {
        ret += 'ZM ';
      }
      ret += arrayToRing(geojson.coordinates);
      return ret;
    };
    var polygonToWKTPolygon = function polygonToWKTPolygon(geojson) {
      var ret = 'POLYGON ';
      if (geojson.coordinates === undefined || geojson.coordinates.length === 0 || geojson.coordinates[0].length === 0) {
        ret += 'EMPTY';
        return ret;
      } else if (geojson.coordinates[0][0].length === 3) {
        if (geojson.properties && geojson.properties.m === true) {
          ret += 'M ';
        } else {
          ret += 'Z ';
        }
      } else if (geojson.coordinates[0][0].length === 4) {
        ret += 'ZM ';
      }
      ret += '(';
      var parts = [];
      for (var i = 0; i < geojson.coordinates.length; i++) {
        parts.push(arrayToRing(geojson.coordinates[i]));
      }
      ret += parts.join(', ');
      ret += ')';
      return ret;
    };
    var multiPointToWKTMultiPoint = function multiPointToWKTMultiPoint(geojson) {
      var ret = 'MULTIPOINT ';
      if (geojson.coordinates === undefined || geojson.coordinates.length === 0 || geojson.coordinates[0].length === 0) {
        ret += 'EMPTY';
        return ret;
      } else if (geojson.coordinates[0].length === 3) {
        if (geojson.properties && geojson.properties.m === true) {
          ret += 'M ';
        } else {
          ret += 'Z ';
        }
      } else if (geojson.coordinates[0].length === 4) {
        ret += 'ZM ';
      }
      ret += arrayToRing(geojson.coordinates);
      return ret;
    };
    var multiLineStringToWKTMultiLineString = function multiLineStringToWKTMultiLineString(geojson) {
      var ret = 'MULTILINESTRING ';
      if (geojson.coordinates === undefined || geojson.coordinates.length === 0 || geojson.coordinates[0].length === 0) {
        ret += 'EMPTY';
        return ret;
      } else if (geojson.coordinates[0][0].length === 3) {
        if (geojson.properties && geojson.properties.m === true) {
          ret += 'M ';
        } else {
          ret += 'Z ';
        }
      } else if (geojson.coordinates[0][0].length === 4) {
        ret += 'ZM ';
      }
      ret += '(';
      var parts = [];
      for (var i = 0; i < geojson.coordinates.length; i++) {
        parts.push(arrayToRing(geojson.coordinates[i]));
      }
      ret += parts.join(', ');
      ret += ')';
      return ret;
    };
    var multiPolygonToWKTMultiPolygon = function multiPolygonToWKTMultiPolygon(geojson) {
      var ret = 'MULTIPOLYGON ';
      if (geojson.coordinates === undefined || geojson.coordinates.length === 0 || geojson.coordinates[0].length === 0) {
        ret += 'EMPTY';
        return ret;
      } else if (geojson.coordinates[0][0][0].length === 3) {
        if (geojson.properties && geojson.properties.m === true) {
          ret += 'M ';
        } else {
          ret += 'Z ';
        }
      } else if (geojson.coordinates[0][0][0].length === 4) {
        ret += 'ZM ';
      }
      ret += '(';
      var inner = [];
      for (var c = 0; c < geojson.coordinates.length; c++) {
        var it = '(';
        var parts = [];
        for (var i = 0; i < geojson.coordinates[c].length; i++) {
          parts.push(arrayToRing(geojson.coordinates[c][i]));
        }
        it += parts.join(', ');
        it += ')';
        inner.push(it);
      }
      ret += inner.join(', ');
      ret += ')';
      return ret;
    };

    /**
     * Converts a GeoJSON geometry or GeometryCollection into a [WKT](https://en.wikipedia.org/wiki/Well-known_text_representation_of_geometry) string.
     * @function
     * @param {object} GeoJSON - The input GeoJSON geometry or GeometryCollection.
     * @return {string} WKT.
     * ```js
     * import { geojsonToWKT } from "@terraformer/wkt"
     *
     * const geojsonPoint = {
     *   "type": "Point",
     *   "coordinates": [-122.6764, 45.5165]
     * }
     *
     * geojsonToWKT(geojsonPoint)
     *
     * >> "POINT (-122.6764 45.5165)"
     * ```
     */
    var geojsonToWKT = function geojsonToWKT(geojson) {
      switch (geojson.type) {
        case 'Point':
          return pointToWKTPoint(geojson);
        case 'LineString':
          return lineStringToWKTLineString(geojson);
        case 'Polygon':
          return polygonToWKTPolygon(geojson);
        case 'MultiPoint':
          return multiPointToWKTMultiPoint(geojson);
        case 'MultiLineString':
          return multiLineStringToWKTMultiLineString(geojson);
        case 'MultiPolygon':
          return multiPolygonToWKTMultiPolygon(geojson);
        case 'GeometryCollection':
          var ret = 'GEOMETRYCOLLECTION';
          var parts = [];
          for (var i = 0; i < geojson.geometries.length; i++) {
            parts.push(geojsonToWKT(geojson.geometries[i]));
          }
          return ret + '(' + parts.join(', ') + ')';
        default:
          throw Error('Unknown Type: ' + geojson.type);
      }
    };

    exports.Parser = Parser;
    exports.geojsonToWKT = geojsonToWKT;
    exports.parser = parser;
    exports.wktToGeoJSON = wktToGeoJSON;

    Object.defineProperty(exports, '__esModule', { value: true });

  }));
