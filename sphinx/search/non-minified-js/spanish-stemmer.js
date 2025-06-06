// Generated from spanish.sbl by Snowball 3.0.1 - https://snowballstem.org/

/**@constructor*/
var SpanishStemmer = function() {
    var base = new BaseStemmer();

    /** @const */ var a_0 = [
        ["", -1, 6],
        ["\u00E1", 0, 1],
        ["\u00E9", 0, 2],
        ["\u00ED", 0, 3],
        ["\u00F3", 0, 4],
        ["\u00FA", 0, 5]
    ];

    /** @const */ var a_1 = [
        ["la", -1, -1],
        ["sela", 0, -1],
        ["le", -1, -1],
        ["me", -1, -1],
        ["se", -1, -1],
        ["lo", -1, -1],
        ["selo", 5, -1],
        ["las", -1, -1],
        ["selas", 7, -1],
        ["les", -1, -1],
        ["los", -1, -1],
        ["selos", 10, -1],
        ["nos", -1, -1]
    ];

    /** @const */ var a_2 = [
        ["ando", -1, 6],
        ["iendo", -1, 6],
        ["yendo", -1, 7],
        ["\u00E1ndo", -1, 2],
        ["i\u00E9ndo", -1, 1],
        ["ar", -1, 6],
        ["er", -1, 6],
        ["ir", -1, 6],
        ["\u00E1r", -1, 3],
        ["\u00E9r", -1, 4],
        ["\u00EDr", -1, 5]
    ];

    /** @const */ var a_3 = [
        ["ic", -1, -1],
        ["ad", -1, -1],
        ["os", -1, -1],
        ["iv", -1, 1]
    ];

    /** @const */ var a_4 = [
        ["able", -1, 1],
        ["ible", -1, 1],
        ["ante", -1, 1]
    ];

    /** @const */ var a_5 = [
        ["ic", -1, 1],
        ["abil", -1, 1],
        ["iv", -1, 1]
    ];

    /** @const */ var a_6 = [
        ["ica", -1, 1],
        ["ancia", -1, 2],
        ["encia", -1, 5],
        ["adora", -1, 2],
        ["osa", -1, 1],
        ["ista", -1, 1],
        ["iva", -1, 9],
        ["anza", -1, 1],
        ["log\u00EDa", -1, 3],
        ["idad", -1, 8],
        ["able", -1, 1],
        ["ible", -1, 1],
        ["ante", -1, 2],
        ["mente", -1, 7],
        ["amente", 13, 6],
        ["acion", -1, 2],
        ["ucion", -1, 4],
        ["aci\u00F3n", -1, 2],
        ["uci\u00F3n", -1, 4],
        ["ico", -1, 1],
        ["ismo", -1, 1],
        ["oso", -1, 1],
        ["amiento", -1, 1],
        ["imiento", -1, 1],
        ["ivo", -1, 9],
        ["ador", -1, 2],
        ["icas", -1, 1],
        ["ancias", -1, 2],
        ["encias", -1, 5],
        ["adoras", -1, 2],
        ["osas", -1, 1],
        ["istas", -1, 1],
        ["ivas", -1, 9],
        ["anzas", -1, 1],
        ["log\u00EDas", -1, 3],
        ["idades", -1, 8],
        ["ables", -1, 1],
        ["ibles", -1, 1],
        ["aciones", -1, 2],
        ["uciones", -1, 4],
        ["adores", -1, 2],
        ["antes", -1, 2],
        ["icos", -1, 1],
        ["ismos", -1, 1],
        ["osos", -1, 1],
        ["amientos", -1, 1],
        ["imientos", -1, 1],
        ["ivos", -1, 9]
    ];

    /** @const */ var a_7 = [
        ["ya", -1, 1],
        ["ye", -1, 1],
        ["yan", -1, 1],
        ["yen", -1, 1],
        ["yeron", -1, 1],
        ["yendo", -1, 1],
        ["yo", -1, 1],
        ["yas", -1, 1],
        ["yes", -1, 1],
        ["yais", -1, 1],
        ["yamos", -1, 1],
        ["y\u00F3", -1, 1]
    ];

    /** @const */ var a_8 = [
        ["aba", -1, 2],
        ["ada", -1, 2],
        ["ida", -1, 2],
        ["ara", -1, 2],
        ["iera", -1, 2],
        ["\u00EDa", -1, 2],
        ["ar\u00EDa", 5, 2],
        ["er\u00EDa", 5, 2],
        ["ir\u00EDa", 5, 2],
        ["ad", -1, 2],
        ["ed", -1, 2],
        ["id", -1, 2],
        ["ase", -1, 2],
        ["iese", -1, 2],
        ["aste", -1, 2],
        ["iste", -1, 2],
        ["an", -1, 2],
        ["aban", 16, 2],
        ["aran", 16, 2],
        ["ieran", 16, 2],
        ["\u00EDan", 16, 2],
        ["ar\u00EDan", 20, 2],
        ["er\u00EDan", 20, 2],
        ["ir\u00EDan", 20, 2],
        ["en", -1, 1],
        ["asen", 24, 2],
        ["iesen", 24, 2],
        ["aron", -1, 2],
        ["ieron", -1, 2],
        ["ar\u00E1n", -1, 2],
        ["er\u00E1n", -1, 2],
        ["ir\u00E1n", -1, 2],
        ["ado", -1, 2],
        ["ido", -1, 2],
        ["ando", -1, 2],
        ["iendo", -1, 2],
        ["ar", -1, 2],
        ["er", -1, 2],
        ["ir", -1, 2],
        ["as", -1, 2],
        ["abas", 39, 2],
        ["adas", 39, 2],
        ["idas", 39, 2],
        ["aras", 39, 2],
        ["ieras", 39, 2],
        ["\u00EDas", 39, 2],
        ["ar\u00EDas", 45, 2],
        ["er\u00EDas", 45, 2],
        ["ir\u00EDas", 45, 2],
        ["es", -1, 1],
        ["ases", 49, 2],
        ["ieses", 49, 2],
        ["abais", -1, 2],
        ["arais", -1, 2],
        ["ierais", -1, 2],
        ["\u00EDais", -1, 2],
        ["ar\u00EDais", 55, 2],
        ["er\u00EDais", 55, 2],
        ["ir\u00EDais", 55, 2],
        ["aseis", -1, 2],
        ["ieseis", -1, 2],
        ["asteis", -1, 2],
        ["isteis", -1, 2],
        ["\u00E1is", -1, 2],
        ["\u00E9is", -1, 1],
        ["ar\u00E9is", 64, 2],
        ["er\u00E9is", 64, 2],
        ["ir\u00E9is", 64, 2],
        ["ados", -1, 2],
        ["idos", -1, 2],
        ["amos", -1, 2],
        ["\u00E1bamos", 70, 2],
        ["\u00E1ramos", 70, 2],
        ["i\u00E9ramos", 70, 2],
        ["\u00EDamos", 70, 2],
        ["ar\u00EDamos", 74, 2],
        ["er\u00EDamos", 74, 2],
        ["ir\u00EDamos", 74, 2],
        ["emos", -1, 1],
        ["aremos", 78, 2],
        ["eremos", 78, 2],
        ["iremos", 78, 2],
        ["\u00E1semos", 78, 2],
        ["i\u00E9semos", 78, 2],
        ["imos", -1, 2],
        ["ar\u00E1s", -1, 2],
        ["er\u00E1s", -1, 2],
        ["ir\u00E1s", -1, 2],
        ["\u00EDs", -1, 2],
        ["ar\u00E1", -1, 2],
        ["er\u00E1", -1, 2],
        ["ir\u00E1", -1, 2],
        ["ar\u00E9", -1, 2],
        ["er\u00E9", -1, 2],
        ["ir\u00E9", -1, 2],
        ["i\u00F3", -1, 2]
    ];

    /** @const */ var a_9 = [
        ["a", -1, 1],
        ["e", -1, 2],
        ["o", -1, 1],
        ["os", -1, 1],
        ["\u00E1", -1, 1],
        ["\u00E9", -1, 2],
        ["\u00ED", -1, 1],
        ["\u00F3", -1, 1]
    ];

    /** @const */ var /** Array<int> */ g_v = [17, 65, 16, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 17, 4, 10];

    var /** number */ I_p2 = 0;
    var /** number */ I_p1 = 0;
    var /** number */ I_pV = 0;


    /** @return {boolean} */
    function r_mark_regions() {
        I_pV = base.limit;
        I_p1 = base.limit;
        I_p2 = base.limit;
        /** @const */ var /** number */ v_1 = base.cursor;
        lab0: {
            lab1: {
                /** @const */ var /** number */ v_2 = base.cursor;
                lab2: {
                    if (!(base.in_grouping(g_v, 97, 252)))
                    {
                        break lab2;
                    }
                    lab3: {
                        /** @const */ var /** number */ v_3 = base.cursor;
                        lab4: {
                            if (!(base.out_grouping(g_v, 97, 252)))
                            {
                                break lab4;
                            }
                            if (!base.go_out_grouping(g_v, 97, 252))
                            {
                                break lab4;
                            }
                            base.cursor++;
                            break lab3;
                        }
                        base.cursor = v_3;
                        if (!(base.in_grouping(g_v, 97, 252)))
                        {
                            break lab2;
                        }
                        if (!base.go_in_grouping(g_v, 97, 252))
                        {
                            break lab2;
                        }
                        base.cursor++;
                    }
                    break lab1;
                }
                base.cursor = v_2;
                if (!(base.out_grouping(g_v, 97, 252)))
                {
                    break lab0;
                }
                lab5: {
                    /** @const */ var /** number */ v_4 = base.cursor;
                    lab6: {
                        if (!(base.out_grouping(g_v, 97, 252)))
                        {
                            break lab6;
                        }
                        if (!base.go_out_grouping(g_v, 97, 252))
                        {
                            break lab6;
                        }
                        base.cursor++;
                        break lab5;
                    }
                    base.cursor = v_4;
                    if (!(base.in_grouping(g_v, 97, 252)))
                    {
                        break lab0;
                    }
                    if (base.cursor >= base.limit)
                    {
                        break lab0;
                    }
                    base.cursor++;
                }
            }
            I_pV = base.cursor;
        }
        base.cursor = v_1;
        /** @const */ var /** number */ v_5 = base.cursor;
        lab7: {
            if (!base.go_out_grouping(g_v, 97, 252))
            {
                break lab7;
            }
            base.cursor++;
            if (!base.go_in_grouping(g_v, 97, 252))
            {
                break lab7;
            }
            base.cursor++;
            I_p1 = base.cursor;
            if (!base.go_out_grouping(g_v, 97, 252))
            {
                break lab7;
            }
            base.cursor++;
            if (!base.go_in_grouping(g_v, 97, 252))
            {
                break lab7;
            }
            base.cursor++;
            I_p2 = base.cursor;
        }
        base.cursor = v_5;
        return true;
    };

    /** @return {boolean} */
    function r_postlude() {
        var /** number */ among_var;
        while(true)
        {
            /** @const */ var /** number */ v_1 = base.cursor;
            lab0: {
                base.bra = base.cursor;
                among_var = base.find_among(a_0);
                base.ket = base.cursor;
                switch (among_var) {
                    case 1:
                        if (!base.slice_from("a"))
                        {
                            return false;
                        }
                        break;
                    case 2:
                        if (!base.slice_from("e"))
                        {
                            return false;
                        }
                        break;
                    case 3:
                        if (!base.slice_from("i"))
                        {
                            return false;
                        }
                        break;
                    case 4:
                        if (!base.slice_from("o"))
                        {
                            return false;
                        }
                        break;
                    case 5:
                        if (!base.slice_from("u"))
                        {
                            return false;
                        }
                        break;
                    case 6:
                        if (base.cursor >= base.limit)
                        {
                            break lab0;
                        }
                        base.cursor++;
                        break;
                }
                continue;
            }
            base.cursor = v_1;
            break;
        }
        return true;
    };

    /** @return {boolean} */
    function r_RV() {
        return I_pV <= base.cursor;
    };

    /** @return {boolean} */
    function r_R1() {
        return I_p1 <= base.cursor;
    };

    /** @return {boolean} */
    function r_R2() {
        return I_p2 <= base.cursor;
    };

    /** @return {boolean} */
    function r_attached_pronoun() {
        var /** number */ among_var;
        base.ket = base.cursor;
        if (base.find_among_b(a_1) == 0)
        {
            return false;
        }
        base.bra = base.cursor;
        among_var = base.find_among_b(a_2);
        if (among_var == 0)
        {
            return false;
        }
        if (!r_RV())
        {
            return false;
        }
        switch (among_var) {
            case 1:
                base.bra = base.cursor;
                if (!base.slice_from("iendo"))
                {
                    return false;
                }
                break;
            case 2:
                base.bra = base.cursor;
                if (!base.slice_from("ando"))
                {
                    return false;
                }
                break;
            case 3:
                base.bra = base.cursor;
                if (!base.slice_from("ar"))
                {
                    return false;
                }
                break;
            case 4:
                base.bra = base.cursor;
                if (!base.slice_from("er"))
                {
                    return false;
                }
                break;
            case 5:
                base.bra = base.cursor;
                if (!base.slice_from("ir"))
                {
                    return false;
                }
                break;
            case 6:
                if (!base.slice_del())
                {
                    return false;
                }
                break;
            case 7:
                if (!(base.eq_s_b("u")))
                {
                    return false;
                }
                if (!base.slice_del())
                {
                    return false;
                }
                break;
        }
        return true;
    };

    /** @return {boolean} */
    function r_standard_suffix() {
        var /** number */ among_var;
        base.ket = base.cursor;
        among_var = base.find_among_b(a_6);
        if (among_var == 0)
        {
            return false;
        }
        base.bra = base.cursor;
        switch (among_var) {
            case 1:
                if (!r_R2())
                {
                    return false;
                }
                if (!base.slice_del())
                {
                    return false;
                }
                break;
            case 2:
                if (!r_R2())
                {
                    return false;
                }
                if (!base.slice_del())
                {
                    return false;
                }
                /** @const */ var /** number */ v_1 = base.limit - base.cursor;
                lab0: {
                    base.ket = base.cursor;
                    if (!(base.eq_s_b("ic")))
                    {
                        base.cursor = base.limit - v_1;
                        break lab0;
                    }
                    base.bra = base.cursor;
                    if (!r_R2())
                    {
                        base.cursor = base.limit - v_1;
                        break lab0;
                    }
                    if (!base.slice_del())
                    {
                        return false;
                    }
                }
                break;
            case 3:
                if (!r_R2())
                {
                    return false;
                }
                if (!base.slice_from("log"))
                {
                    return false;
                }
                break;
            case 4:
                if (!r_R2())
                {
                    return false;
                }
                if (!base.slice_from("u"))
                {
                    return false;
                }
                break;
            case 5:
                if (!r_R2())
                {
                    return false;
                }
                if (!base.slice_from("ente"))
                {
                    return false;
                }
                break;
            case 6:
                if (!r_R1())
                {
                    return false;
                }
                if (!base.slice_del())
                {
                    return false;
                }
                /** @const */ var /** number */ v_2 = base.limit - base.cursor;
                lab1: {
                    base.ket = base.cursor;
                    among_var = base.find_among_b(a_3);
                    if (among_var == 0)
                    {
                        base.cursor = base.limit - v_2;
                        break lab1;
                    }
                    base.bra = base.cursor;
                    if (!r_R2())
                    {
                        base.cursor = base.limit - v_2;
                        break lab1;
                    }
                    if (!base.slice_del())
                    {
                        return false;
                    }
                    switch (among_var) {
                        case 1:
                            base.ket = base.cursor;
                            if (!(base.eq_s_b("at")))
                            {
                                base.cursor = base.limit - v_2;
                                break lab1;
                            }
                            base.bra = base.cursor;
                            if (!r_R2())
                            {
                                base.cursor = base.limit - v_2;
                                break lab1;
                            }
                            if (!base.slice_del())
                            {
                                return false;
                            }
                            break;
                    }
                }
                break;
            case 7:
                if (!r_R2())
                {
                    return false;
                }
                if (!base.slice_del())
                {
                    return false;
                }
                /** @const */ var /** number */ v_3 = base.limit - base.cursor;
                lab2: {
                    base.ket = base.cursor;
                    if (base.find_among_b(a_4) == 0)
                    {
                        base.cursor = base.limit - v_3;
                        break lab2;
                    }
                    base.bra = base.cursor;
                    if (!r_R2())
                    {
                        base.cursor = base.limit - v_3;
                        break lab2;
                    }
                    if (!base.slice_del())
                    {
                        return false;
                    }
                }
                break;
            case 8:
                if (!r_R2())
                {
                    return false;
                }
                if (!base.slice_del())
                {
                    return false;
                }
                /** @const */ var /** number */ v_4 = base.limit - base.cursor;
                lab3: {
                    base.ket = base.cursor;
                    if (base.find_among_b(a_5) == 0)
                    {
                        base.cursor = base.limit - v_4;
                        break lab3;
                    }
                    base.bra = base.cursor;
                    if (!r_R2())
                    {
                        base.cursor = base.limit - v_4;
                        break lab3;
                    }
                    if (!base.slice_del())
                    {
                        return false;
                    }
                }
                break;
            case 9:
                if (!r_R2())
                {
                    return false;
                }
                if (!base.slice_del())
                {
                    return false;
                }
                /** @const */ var /** number */ v_5 = base.limit - base.cursor;
                lab4: {
                    base.ket = base.cursor;
                    if (!(base.eq_s_b("at")))
                    {
                        base.cursor = base.limit - v_5;
                        break lab4;
                    }
                    base.bra = base.cursor;
                    if (!r_R2())
                    {
                        base.cursor = base.limit - v_5;
                        break lab4;
                    }
                    if (!base.slice_del())
                    {
                        return false;
                    }
                }
                break;
        }
        return true;
    };

    /** @return {boolean} */
    function r_y_verb_suffix() {
        if (base.cursor < I_pV)
        {
            return false;
        }
        /** @const */ var /** number */ v_1 = base.limit_backward;
        base.limit_backward = I_pV;
        base.ket = base.cursor;
        if (base.find_among_b(a_7) == 0)
        {
            base.limit_backward = v_1;
            return false;
        }
        base.bra = base.cursor;
        base.limit_backward = v_1;
        if (!(base.eq_s_b("u")))
        {
            return false;
        }
        if (!base.slice_del())
        {
            return false;
        }
        return true;
    };

    /** @return {boolean} */
    function r_verb_suffix() {
        var /** number */ among_var;
        if (base.cursor < I_pV)
        {
            return false;
        }
        /** @const */ var /** number */ v_1 = base.limit_backward;
        base.limit_backward = I_pV;
        base.ket = base.cursor;
        among_var = base.find_among_b(a_8);
        if (among_var == 0)
        {
            base.limit_backward = v_1;
            return false;
        }
        base.bra = base.cursor;
        base.limit_backward = v_1;
        switch (among_var) {
            case 1:
                /** @const */ var /** number */ v_2 = base.limit - base.cursor;
                lab0: {
                    if (!(base.eq_s_b("u")))
                    {
                        base.cursor = base.limit - v_2;
                        break lab0;
                    }
                    /** @const */ var /** number */ v_3 = base.limit - base.cursor;
                    if (!(base.eq_s_b("g")))
                    {
                        base.cursor = base.limit - v_2;
                        break lab0;
                    }
                    base.cursor = base.limit - v_3;
                }
                base.bra = base.cursor;
                if (!base.slice_del())
                {
                    return false;
                }
                break;
            case 2:
                if (!base.slice_del())
                {
                    return false;
                }
                break;
        }
        return true;
    };

    /** @return {boolean} */
    function r_residual_suffix() {
        var /** number */ among_var;
        base.ket = base.cursor;
        among_var = base.find_among_b(a_9);
        if (among_var == 0)
        {
            return false;
        }
        base.bra = base.cursor;
        switch (among_var) {
            case 1:
                if (!r_RV())
                {
                    return false;
                }
                if (!base.slice_del())
                {
                    return false;
                }
                break;
            case 2:
                if (!r_RV())
                {
                    return false;
                }
                if (!base.slice_del())
                {
                    return false;
                }
                /** @const */ var /** number */ v_1 = base.limit - base.cursor;
                lab0: {
                    base.ket = base.cursor;
                    if (!(base.eq_s_b("u")))
                    {
                        base.cursor = base.limit - v_1;
                        break lab0;
                    }
                    base.bra = base.cursor;
                    /** @const */ var /** number */ v_2 = base.limit - base.cursor;
                    if (!(base.eq_s_b("g")))
                    {
                        base.cursor = base.limit - v_1;
                        break lab0;
                    }
                    base.cursor = base.limit - v_2;
                    if (!r_RV())
                    {
                        base.cursor = base.limit - v_1;
                        break lab0;
                    }
                    if (!base.slice_del())
                    {
                        return false;
                    }
                }
                break;
        }
        return true;
    };

    this.stem = /** @return {boolean} */ function() {
        r_mark_regions();
        base.limit_backward = base.cursor; base.cursor = base.limit;
        /** @const */ var /** number */ v_1 = base.limit - base.cursor;
        r_attached_pronoun();
        base.cursor = base.limit - v_1;
        /** @const */ var /** number */ v_2 = base.limit - base.cursor;
        lab0: {
            lab1: {
                /** @const */ var /** number */ v_3 = base.limit - base.cursor;
                lab2: {
                    if (!r_standard_suffix())
                    {
                        break lab2;
                    }
                    break lab1;
                }
                base.cursor = base.limit - v_3;
                lab3: {
                    if (!r_y_verb_suffix())
                    {
                        break lab3;
                    }
                    break lab1;
                }
                base.cursor = base.limit - v_3;
                if (!r_verb_suffix())
                {
                    break lab0;
                }
            }
        }
        base.cursor = base.limit - v_2;
        /** @const */ var /** number */ v_4 = base.limit - base.cursor;
        r_residual_suffix();
        base.cursor = base.limit - v_4;
        base.cursor = base.limit_backward;
        /** @const */ var /** number */ v_5 = base.cursor;
        r_postlude();
        base.cursor = v_5;
        return true;
    };

    /**@return{string}*/
    this['stemWord'] = function(/**string*/word) {
        base.setCurrent(word);
        this.stem();
        return base.getCurrent();
    };
};
